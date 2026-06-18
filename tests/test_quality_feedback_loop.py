from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.feedback_loop import QualityFeedbackLoopBuilder, QualityFeedbackLoopConfig


class QualityFeedbackLoopBuilderTests(unittest.TestCase):
    def _build_run_report(self, temp_root: Path) -> dict[str, object]:
        bundle_a = {
            'skill': {'skill_id': 'skill-a'},
            'adapter_metadata': {
                'quality_scores': {
                    'traceability_score': 0.81,
                    'actionability_score': 0.72,
                    'coverage_score': 0.76,
                    'consistency_score': 0.7,
                    'noise_score': 0.79,
                    'novelty_score': 0.6,
                    'overall_score': 0.74,
                },
                'review_feedback': {
                    'review_task_id': 'task-a',
                    'skill_id': 'skill-a',
                    'decision': 'review_required',
                    'status': 'review_pending',
                    'reason_codes': ['Q_TRACEABILITY_LOW', 'Q_ACTIONABILITY_LOW'],
                    'categories': ['missing_evidence', 'non_actionable_steps'],
                    'atom_actions': [
                        {
                            'action_code': 'ATOM_ADD_EVIDENCE_GROUNDED',
                            'target': 'atom',
                            'intent': 'add_atom',
                            'reason_code': 'Q_TRACEABILITY_LOW',
                            'params': {'strategy': 'backfill_missing_evidence_refs'},
                        }
                    ],
                    'graph_actions': [
                        {
                            'action_code': 'GRAPH_REWRITE_NON_ACTIONABLE_STEPS',
                            'target': 'graph',
                            'intent': 'rewrite_steps',
                            'reason_code': 'Q_ACTIONABILITY_LOW',
                            'params': {'require_action_verb': True},
                        }
                    ],
                    'policy_actions': [],
                    'revision_suggestions': ['S_ADD_TRACEABLE_EVIDENCE'],
                    'follow_up_checks': ['CHECK_TRACEABILITY_CHAIN'],
                    'score_snapshot': {'overall_score': 0.74},
                    'thresholds': {'auto_publish_min_overall': 0.82},
                },
                'review_task': {
                    'review_task_id': 'task-a',
                    'skill_id': 'skill-a',
                    'decision': 'review_required',
                    'status': 'review_pending',
                    'reason_codes': ['Q_TRACEABILITY_LOW', 'Q_ACTIONABILITY_LOW'],
                },
            },
        }

        bundle_b = {
            'skill': {'skill_id': 'skill-b'},
            'adapter_metadata': {
                'quality_scores': {
                    'traceability_score': 0.22,
                    'actionability_score': 0.2,
                    'coverage_score': 0.25,
                    'consistency_score': 0.18,
                    'noise_score': 0.21,
                    'novelty_score': 0.45,
                    'overall_score': 0.23,
                },
                'review_feedback': {
                    'review_task_id': 'task-b',
                    'skill_id': 'skill-b',
                    'decision': 'reject',
                    'status': 'rejected',
                    'reason_codes': ['R_TRACEABILITY_CRITICAL'],
                    'categories': ['missing_evidence'],
                    'atom_actions': [
                        {
                            'action_code': 'ATOM_ADD_EVIDENCE_GROUNDED',
                            'target': 'atom',
                            'intent': 'add_atom',
                            'reason_code': 'R_TRACEABILITY_CRITICAL',
                            'params': {'strategy': 'backfill_missing_evidence_refs'},
                        }
                    ],
                    'graph_actions': [],
                    'policy_actions': [
                        {
                            'action_code': 'POLICY_ESCALATE_REJECTION_REVIEW',
                            'target': 'policy',
                            'intent': 'escalate_manual_review',
                            'reason_code': 'REJECT_FALLBACK',
                            'params': {'priority': 'high'},
                        }
                    ],
                    'revision_suggestions': ['S_REBUILD_FROM_EVIDENCE'],
                    'follow_up_checks': ['CHECK_REJECTION_ROOT_CAUSE'],
                    'score_snapshot': {'overall_score': 0.23},
                    'thresholds': {'reject_max_overall': 0.35},
                },
                'review_task': {
                    'review_task_id': 'task-b',
                    'skill_id': 'skill-b',
                    'decision': 'reject',
                    'status': 'rejected',
                    'reason_codes': ['R_TRACEABILITY_CRITICAL'],
                },
            },
        }

        bundle_a_path = temp_root / 'bundle-a.json'
        bundle_b_path = temp_root / 'bundle-b.json'
        bundle_a_path.write_text(json.dumps(bundle_a, ensure_ascii=False, indent=2), encoding='utf-8')
        bundle_b_path.write_text(json.dumps(bundle_b, ensure_ascii=False, indent=2), encoding='utf-8')

        return {
            'run_id': 'controlled-trial-test-run',
            'samples': [
                {
                    'sample_id': 'sample-a',
                    'modality': 'text',
                    'approved_bundle_path': str(bundle_a_path),
                    'loop_metrics': {
                        'review_outcome': 'approved',
                        'reviewer_edit_distance_pct': 31.0,
                    },
                },
                {
                    'sample_id': 'sample-b',
                    'modality': 'video',
                    'approved_bundle_path': str(bundle_b_path),
                    'loop_metrics': {
                        'review_outcome': 'rejected',
                        'reviewer_edit_distance_pct': 42.0,
                    },
                },
            ],
        }

    def test_builder_emits_remediation_regression_and_calibration_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            run_report = self._build_run_report(root)
            builder = QualityFeedbackLoopBuilder(
                QualityFeedbackLoopConfig(repeat_threshold=2, reviewer_edit_distance_threshold=25.0)
            )

            report = builder.build_from_run_report(run_report, base_dir=root)

            self.assertEqual(report.get('schema_version'), 'quality_feedback_loop.v1')
            summary = report.get('summary', {})
            self.assertEqual(summary.get('sample_count'), 2)
            self.assertEqual(summary.get('remediation_plan_count'), 2)
            self.assertEqual(summary.get('calibration_sample_count'), 2)

            remediation_plans = report.get('remediation_plans', [])
            self.assertEqual(len(remediation_plans), 2)
            self.assertEqual(remediation_plans[0].get('next_action'), 'run_targeted_remediation')
            self.assertEqual(remediation_plans[1].get('next_action'), 'rebuild_from_evidence')

            regression_cases = report.get('regression_cases', [])
            self.assertTrue(regression_cases)
            case_keys = {item.get('defect_key') for item in regression_cases}
            self.assertIn('REVIEWER_EDIT_DISTANCE_HIGH', case_keys)

            calibration_manifest = report.get('calibration_manifest', {})
            self.assertEqual(calibration_manifest.get('manifest_id'), 'quality-feedback-loop-calibration')
            samples = calibration_manifest.get('samples', [])
            self.assertEqual(len(samples), 2)
            decisions = {item.get('reviewer_judgement', {}).get('decision') for item in samples}
            self.assertIn('auto_publish', decisions)
            self.assertIn('reject', decisions)

            markdown = builder.render_summary_markdown(report)
            self.assertIn('Quality Feedback Loop Summary', markdown)
            self.assertIn('Regression cases generated: `', markdown)


if __name__ == '__main__':
    unittest.main()
