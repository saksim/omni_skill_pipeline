from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.interfaces import ReviewQueueRepository
from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    DistillBundle,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    ReviewDecision,
    ReviewStatus,
    ReviewTask,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.repository import FileArtifactRepository


def _build_bundle_with_review(decision: ReviewDecision) -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://review-queue-source')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Validate review queue persistence contract.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Derive review actions from evidence.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Review Queue Skill',
        goal='Validate review queue persistence.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Persist and query review task.', why='queue contract')],
        evidence_refs=[evidence.evidence_id],
    )

    status = ReviewStatus.REVIEW_PENDING
    if decision == ReviewDecision.AUTO_PUBLISH:
        status = ReviewStatus.PUBLISHED
    elif decision == ReviewDecision.REJECT:
        status = ReviewStatus.REJECTED

    reason_codes = ['Q_MANUAL_REVIEW_DEFAULT'] if decision == ReviewDecision.REVIEW_REQUIRED else ['A_MEETS_ALL_THRESHOLDS']
    review_task = ReviewTask(
        skill_id=skill.skill_id,
        decision=decision,
        reason_codes=reason_codes,
        revision_suggestions=['S_MANUAL_REVIEW_REQUIRED'],
        score_snapshot={'overall_score': 0.62},
        thresholds={'auto_publish_min': 0.75},
        status=status,
    )

    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Review Queue Skill\n\n- Persist and query review task.\n',
        review_task=review_task,
        quality_scores={'overall_score': 0.62},
        adapter_metadata={
            'review_policy': {
                'decision': decision.value,
                'reason_codes': reason_codes,
                'score_snapshot': {'overall_score': 0.62},
                'thresholds': {'auto_publish_min': 0.75},
            },
            'review_task': review_task.to_dict(),
        },
    )


class ReviewQueueRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('review_queue_repo_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_file_repository_declares_review_queue_protocol(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        self.assertIsInstance(repository, ReviewQueueRepository)

    def test_review_required_task_is_queryable_and_consumable(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_bundle_with_review(ReviewDecision.REVIEW_REQUIRED)

        artifacts = repository.save_bundle(bundle)

        self.assertIn('review_queue_item', artifacts)
        self.assertTrue(Path(artifacts['review_queue_item']).exists())

        pending = repository.list_review_queue()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['review_task_id'], bundle.review_task.review_task_id)
        self.assertEqual(pending[0]['decision'], ReviewDecision.REVIEW_REQUIRED.value)
        self.assertEqual(pending[0]['queue_status'], 'pending')

        consumed = repository.consume_review_task(consumer='integration-reviewer')
        self.assertIsNotNone(consumed)
        self.assertEqual(consumed['review_task_id'], bundle.review_task.review_task_id)
        self.assertEqual(consumed['queue_status'], 'consumed')
        self.assertEqual(consumed['claimed_by'], 'integration-reviewer')

        self.assertEqual(repository.list_review_queue(), [])
        consumed_items = repository.list_review_queue(queue_status='consumed')
        self.assertEqual(len(consumed_items), 1)
        self.assertEqual(consumed_items[0]['review_task_id'], bundle.review_task.review_task_id)

    def test_claim_by_id_and_close_moves_task_to_closed_bucket(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_bundle_with_review(ReviewDecision.REVIEW_REQUIRED)
        repository.save_bundle(bundle)

        review_task_id = bundle.review_task.review_task_id
        claimed = repository.claim_review_task(review_task_id=review_task_id, consumer='review-ops')
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed['review_task_id'], review_task_id)
        self.assertEqual(claimed['queue_status'], 'consumed')
        self.assertEqual(claimed['claimed_by'], 'review-ops')

        closed = repository.close_review_task(
            review_task_id,
            status='published',
            closed_by='qa-lead',
            review_notes='approved after manual review',
        )
        self.assertIsNotNone(closed)
        self.assertEqual(closed['review_task_id'], review_task_id)
        self.assertEqual(closed['queue_status'], 'closed')
        self.assertEqual(closed['status'], 'published')
        self.assertEqual(closed['closed_by'], 'qa-lead')
        self.assertEqual(closed['review_notes'], 'approved after manual review')

        self.assertEqual(repository.list_review_queue(queue_status='pending'), [])
        self.assertEqual(repository.list_review_queue(queue_status='consumed'), [])
        closed_items = repository.list_review_queue(queue_status='closed')
        self.assertEqual(len(closed_items), 1)
        self.assertEqual(closed_items[0]['review_task_id'], review_task_id)

    def test_close_persists_structured_decision_reason_codes_and_reviewer_edits(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_bundle_with_review(ReviewDecision.REVIEW_REQUIRED)
        repository.save_bundle(bundle)

        review_task_id = bundle.review_task.review_task_id
        repository.claim_review_task(review_task_id=review_task_id, consumer='review-ops')

        closed = repository.close_review_task(
            review_task_id,
            status='published',
            closed_by='review-lead',
            review_notes='approved with minor edits',
            decision='approved',
            reason_codes=['SAFE', 'MANUAL_CHECK_COMPLETE'],
            reviewer_edits={'skill_markdown_patch': 'typo fix'},
        )
        self.assertIsNotNone(closed)
        self.assertEqual(closed['decision'], 'approve')
        self.assertEqual(closed['reason_codes'], ['SAFE', 'MANUAL_CHECK_COMPLETE'])
        self.assertEqual(closed['reviewer_edits'], {'skill_markdown_patch': 'typo fix'})

        closed_items = repository.list_review_queue(queue_status='closed')
        self.assertEqual(closed_items[0]['decision'], 'approve')
        self.assertEqual(closed_items[0]['reason_codes'], ['SAFE', 'MANUAL_CHECK_COMPLETE'])
        self.assertEqual(closed_items[0]['reviewer_edits'], {'skill_markdown_patch': 'typo fix'})

    def test_update_review_task_decision_maps_to_structured_status(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_bundle_with_review(ReviewDecision.REVIEW_REQUIRED)
        repository.save_bundle(bundle)
        review_task_id = bundle.review_task.review_task_id
        repository.claim_review_task(review_task_id=review_task_id, consumer='review-ops')

        needs_rework = repository.update_review_task_decision(
            review_task_id,
            decision='needs rework',
            reviewer='qa-reviewer',
            reason_codes=['TRACEABILITY_LOW'],
            review_notes='add evidence links',
            reviewer_edits={'checklist_diff': 'added validation step'},
        )
        self.assertIsNotNone(needs_rework)
        self.assertEqual(needs_rework['decision'], 'needs_rework')
        self.assertEqual(needs_rework['status'], 'needs_rework')
        self.assertEqual(needs_rework['closed_by'], 'qa-reviewer')
        self.assertEqual(needs_rework['reason_codes'], ['TRACEABILITY_LOW'])
        self.assertEqual(needs_rework['reviewer_edits'], {'checklist_diff': 'added validation step'})

    def test_non_review_required_task_is_not_enqueued(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_bundle_with_review(ReviewDecision.AUTO_PUBLISH)

        artifacts = repository.save_bundle(bundle)

        self.assertNotIn('review_queue_item', artifacts)
        self.assertEqual(repository.list_review_queue(), [])
        self.assertIsNone(repository.consume_review_task())


if __name__ == '__main__':
    unittest.main()
