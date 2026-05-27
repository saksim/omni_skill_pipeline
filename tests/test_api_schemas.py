from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.api_schemas import (
    AudioDistillRequestSchema,
    ConsoleViewsRequestSchema,
    CorpusAssetRequestSchema,
    CorpusDistillRequestSchema,
    DistillGoalSchema,
    ImageDistillRequestSchema,
    ReviewQueueCloseRequestSchema,
    ReviewQueueDecisionRequestSchema,
    TabularDistillRequestSchema,
    TextDistillRequestSchema,
    VideoDistillRequestSchema,
)

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover
    FastAPI = None


class ApiSchemaTests(unittest.TestCase):
    def test_request_schema_imports_and_validates_minimal_payloads(self) -> None:
        goal = DistillGoalSchema.model_validate({})
        self.assertEqual(goal.domain, 'general')

        text_request = TextDistillRequestSchema.model_validate({'content': 'incident timeline'})
        audio_request = AudioDistillRequestSchema.model_validate({'transcript': 'verify recovery'})
        image_request = ImageDistillRequestSchema.model_validate({'image_path': 'artifacts/diagram.png'})
        tabular_request = TabularDistillRequestSchema.model_validate({'file_path': 'artifacts/latency.csv'})
        video_request = VideoDistillRequestSchema.model_validate({'video_path': 'artifacts/demo.mp4'})
        corpus_request = CorpusDistillRequestSchema.model_validate(
            {
                'name': '  launch readiness corpus  ',
                'assets': [{'source_uri': '  docs/runbook.md  ', 'modality': 'text'}],
                'tags': [' launch ', ' ', 'beta'],
            }
        )

        self.assertEqual(text_request.goal.domain, 'general')
        self.assertEqual(audio_request.goal.domain, 'general')
        self.assertEqual(image_request.image_path, 'artifacts/diagram.png')
        self.assertEqual(tabular_request.max_series, 6)
        self.assertIsNone(video_request.max_keyframes)
        self.assertEqual(corpus_request.name, 'launch readiness corpus')
        self.assertEqual(corpus_request.assets[0], CorpusAssetRequestSchema(source_uri='docs/runbook.md', modality='text'))
        self.assertEqual(corpus_request.assets[0].role, 'primary')
        self.assertEqual(corpus_request.tags, ['launch', 'beta'])

    def test_request_schema_validation_matches_runtime_contracts(self) -> None:
        with self.assertRaises(ValidationError):
            TextDistillRequestSchema.model_validate({})

        with self.assertRaises(ValidationError):
            AudioDistillRequestSchema.model_validate({})

        with self.assertRaises(ValidationError):
            CorpusDistillRequestSchema.model_validate({'assets': []})

        with self.assertRaises(ValidationError):
            TabularDistillRequestSchema.model_validate({'file_path': 'metrics.csv', 'max_series': 0})

        with self.assertRaises(ValidationError):
            VideoDistillRequestSchema.model_validate({'video_path': 'demo.mp4', 'scene_threshold': 1.5})

    def test_review_queue_decision_schema_normalizes_decision_and_reason_codes(self) -> None:
        payload = ReviewQueueDecisionRequestSchema.model_validate(
            {
                'decision': 'needs-rework',
                'reviewer': 'ops-reviewer',
                'reason_codes': [' REVIEW_POLICY_MISMATCH ', ''],
                'review_notes': 'clarify rollback precondition',
                'reviewer_edits': {'skill_markdown_patch': '...'},
            }
        )
        self.assertEqual(payload.decision, 'needs_rework')
        self.assertEqual(payload.reviewer, 'ops-reviewer')
        self.assertEqual(payload.reason_codes, ['REVIEW_POLICY_MISMATCH'])
        self.assertEqual(payload.review_notes, 'clarify rollback precondition')
        self.assertEqual(payload.reviewer_edits, {'skill_markdown_patch': '...'})

        close_payload = ReviewQueueCloseRequestSchema.model_validate(
            {
                'status': 'published',
                'closed_by': 'ops-lead',
                'decision': 'approved',
                'reason_codes': ['SAFE'],
                'reviewer_edits': {'checklist_diff': 'none'},
            }
        )
        self.assertEqual(close_payload.decision, 'approve')
        self.assertEqual(close_payload.reason_codes, ['SAFE'])
        self.assertEqual(close_payload.reviewer_edits, {'checklist_diff': 'none'})

    def test_review_queue_decision_schema_rejects_invalid_decision(self) -> None:
        with self.assertRaises(ValidationError):
            ReviewQueueDecisionRequestSchema.model_validate({'decision': 'ship-it'})

    def test_console_views_schema_normalizes_and_validates(self) -> None:
        payload = ConsoleViewsRequestSchema.model_validate(
            {
                'organization_id': ' org-a ',
                'project_id': ' proj-1 ',
                'queue_status': 'CLOSED',
                'limit': 25,
            }
        )
        self.assertEqual(payload.organization_id, 'org-a')
        self.assertEqual(payload.project_id, 'proj-1')
        self.assertEqual(payload.queue_status, 'closed')
        self.assertEqual(payload.limit, 25)

        with self.assertRaises(ValidationError):
            ConsoleViewsRequestSchema.model_validate({'queue_status': 'invalid'})

    @unittest.skipIf(FastAPI is None, 'fastapi is not installed')
    def test_openapi_schema_exposes_all_request_models(self) -> None:
        app = FastAPI(title='schema-probe')

        @app.post('/v1/distill/text')
        def distill_text(payload: TextDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/distill/audio')
        def distill_audio(payload: AudioDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/distill/image')
        def distill_image(payload: ImageDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/distill/tabular')
        def distill_tabular(payload: TabularDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/distill/video')
        def distill_video(payload: VideoDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/distill/corpus')
        def distill_corpus(payload: CorpusDistillRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        @app.post('/v1/console/views')
        def console_views(payload: ConsoleViewsRequestSchema) -> dict[str, bool]:
            return {'ok': True}

        openapi = app.openapi()
        schemas = set(openapi['components']['schemas'])

        for expected in (
            'AudioDistillRequestSchema',
            'ConsoleViewsRequestSchema',
            'CorpusAssetRequestSchema',
            'CorpusDistillRequestSchema',
            'DistillGoalSchema',
            'ImageDistillRequestSchema',
            'TabularDistillRequestSchema',
            'TextDistillRequestSchema',
            'VideoDistillRequestSchema',
        ):
            self.assertTrue(any(name.startswith(expected) for name in schemas), msg='Missing schema for %s' % expected)

        for path, expected in (
            ('/v1/distill/text', 'TextDistillRequestSchema'),
            ('/v1/distill/audio', 'AudioDistillRequestSchema'),
            ('/v1/distill/image', 'ImageDistillRequestSchema'),
            ('/v1/distill/tabular', 'TabularDistillRequestSchema'),
            ('/v1/distill/video', 'VideoDistillRequestSchema'),
            ('/v1/distill/corpus', 'CorpusDistillRequestSchema'),
        ):
            ref = openapi['paths'][path]['post']['requestBody']['content']['application/json']['schema']['$ref']
            self.assertIn(expected, ref)


if __name__ == '__main__':
    unittest.main()
