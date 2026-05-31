from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'roadmap_ext.py'


class RoadmapExtensionValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_roadmap_extension_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'roadmap-extension-plan.json'
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
                'Selected stages: retrieval_layer, lifecycle_engine, publication_expansion, review_queue_surface',
                completed.stdout,
            )
            self.assertIn('tests.test_similarity_retrieval.SimilarityRetrievalTests', completed.stdout)
            self.assertIn(
                'tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests',
                completed.stdout,
            )
            self.assertIn('tests.test_publication_builder.PublicationBuilderTests', completed.stdout)
            self.assertIn(
                'tests.test_publication_orchestrator_split.PublicationHarmonizerTests',
                completed.stdout,
            )
            self.assertIn(
                'tests.test_publication_orchestrator_split.PublicationOrchestratorTests',
                completed.stdout,
            )
            self.assertIn('tests.test_review_queue_repository.ReviewQueueRepositoryTests', completed.stdout)
            self.assertIn('tests.test_review_queue_integration.ReviewQueueIntegrationTests', completed.stdout)
            self.assertIn('tests.test_api_review_queue.ApiReviewQueueEndpointTests', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 4)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'retrieval_layer',
                    'lifecycle_engine',
                    'publication_expansion',
                    'review_queue_surface',
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
                'retrieval_layer',
                'review_queue_surface',
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
        self.assertIn('Selected stages: retrieval_layer, review_queue_surface', completed.stdout)
        self.assertIn('tests.test_similarity_retrieval.SimilarityRetrievalTests', completed.stdout)
        self.assertIn('tests.test_review_queue_repository.ReviewQueueRepositoryTests', completed.stdout)
        self.assertIn('tests.test_review_queue_integration.ReviewQueueIntegrationTests', completed.stdout)
        self.assertIn('tests.test_api_review_queue.ApiReviewQueueEndpointTests', completed.stdout)
        self.assertNotIn('tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests', completed.stdout)
        self.assertNotIn('tests.test_publication_builder.PublicationBuilderTests', completed.stdout)
        self.assertNotIn(
            'tests.test_publication_orchestrator_split.PublicationOrchestratorTests',
            completed.stdout,
        )


if __name__ == '__main__':
    unittest.main()
