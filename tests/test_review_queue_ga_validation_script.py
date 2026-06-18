from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'ga_review_queue.py'


class ReviewQueueGaValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_review_queue_ga_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'review-queue-ga-plan.json'
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
                'Selected stages: review_queue_repository, review_queue_service_flow, review_queue_api, review_feedback, review_feedback_consumer',
                completed.stdout,
            )
            self.assertIn('tests.test_review_queue_repository.ReviewQueueRepositoryTests', completed.stdout)
            self.assertIn('tests.test_review_queue_integration.ReviewQueueIntegrationTests.test_service_review_required_flow_persists_queryable_review_queue', completed.stdout)
            self.assertIn('tests.test_api_review_queue.ApiReviewQueueEndpointTests', completed.stdout)
            self.assertIn('tests.test_review_feedback.ReviewFeedbackEngineTests', completed.stdout)
            self.assertIn('tests.test_review_feedback_consumer.ReviewFeedbackConsumerTests', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 5)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'review_queue_repository',
                    'review_queue_service_flow',
                    'review_queue_api',
                    'review_feedback',
                    'review_feedback_consumer',
                ],
            )

    def test_script_respects_stage_selection(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'review_queue_api',
                'review_feedback_consumer',
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
        self.assertIn('Selected stages: review_queue_api, review_feedback_consumer', completed.stdout)
        self.assertIn('tests.test_api_review_queue.ApiReviewQueueEndpointTests', completed.stdout)
        self.assertIn('tests.test_review_feedback_consumer.ReviewFeedbackConsumerTests', completed.stdout)
        self.assertNotIn('tests.test_review_queue_repository.ReviewQueueRepositoryTests', completed.stdout)
        self.assertNotIn('tests.test_review_queue_integration.ReviewQueueIntegrationTests.test_service_review_required_flow_persists_queryable_review_queue', completed.stdout)
        self.assertNotIn('tests.test_review_feedback.ReviewFeedbackEngineTests', completed.stdout)


if __name__ == '__main__':
    unittest.main()
