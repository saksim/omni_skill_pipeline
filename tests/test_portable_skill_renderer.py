from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import (
    Audience,
    DecisionNode,
    Modality,
    ReviewStatus,
    SkillDocument,
    SkillGraph,
    SkillStep,
    StepNode,
    VerificationNode,
)
from omni_skill_pipeline.publication import PortableSkillRenderer


class PortableSkillRendererTests(unittest.TestCase):
    def _build_skill(self) -> SkillDocument:
        return SkillDocument(
            name='Incident Response Skill',
            goal='Stabilize service and document decisions.',
            source_modality=Modality.VIDEO,
            audience=Audience.EXPERT,
            trigger=['error rate exceeds baseline'],
            inputs=['incident timeline', 'deployment diff'],
            preconditions=['on-call reviewer assigned'],
            steps=[
                SkillStep(step=1, action='Rebuild timeline from logs and transcript.', why='Establish shared facts.'),
                SkillStep(step=2, action='Rollback risky deployment.', why='Reduce user impact quickly.'),
            ],
            decision_rules=['if error rate stays high after rollback -> escalate incident command'],
            anti_patterns=['Do not patch and rollback simultaneously.'],
            verification=['Confirm error rate and latency return below baseline.'],
            evidence_refs=['ev-1', 'ev-2'],
            summary='Controlled trial incident handling procedure.',
            tags=['incident', 'video', 'ops'],
            review_status=ReviewStatus.REVIEW_PENDING,
            skill_id='skill-incident-response',
        )

    def _build_graph(self) -> SkillGraph:
        return SkillGraph(
            graph_id='graph-incident-response',
            name='Incident Response Graph',
            goal='Transform multi-asset incident evidence into executable response.',
            source_modalities=[Modality.VIDEO, Modality.AUDIO, Modality.IMAGE, Modality.TEXT],
            audience=Audience.EXPERT,
            summary='Graph-level summary for controlled trial rendering.',
            trigger=['error rate exceeds baseline'],
            inputs=['incident timeline', 'deployment diff'],
            preconditions=['on-call reviewer assigned'],
            steps=[
                StepNode(
                    step=1,
                    action='Rebuild timeline from logs and transcript.',
                    why='Establish shared facts.',
                    evidence_refs=['ev-1'],
                    node_id='step-1',
                ),
                StepNode(
                    step=2,
                    action='Rollback risky deployment.',
                    why='Reduce user impact quickly.',
                    evidence_refs=['ev-2'],
                    node_id='step-2',
                ),
            ],
            decisions=[
                DecisionNode(
                    condition='error rate stays high after rollback',
                    decision='escalate incident command',
                    rationale='Potential cross-service issue.',
                    evidence_refs=['ev-3'],
                    node_id='decision-1',
                )
            ],
            verifications=[
                VerificationNode(
                    check='Confirm error rate and latency return below baseline.',
                    expected='Both metrics stabilize within 10 minutes.',
                    evidence_refs=['ev-4'],
                    node_id='verification-1',
                )
            ],
            evidence_refs=['ev-root'],
        )

    def test_renderer_outputs_required_sections_and_frontmatter(self) -> None:
        renderer = PortableSkillRenderer()
        result = renderer.render(skill=self._build_skill(), graph=self._build_graph())

        self.assertIn('---', result.skill_markdown)
        self.assertIn('name: "Incident Response Skill"', result.skill_markdown)
        self.assertIn('description: "Use when', result.skill_markdown)
        self.assertIn('## Workflow', result.skill_markdown)
        self.assertIn('## Decision Rules', result.skill_markdown)
        self.assertIn('## Validation', result.skill_markdown)
        self.assertIn('## Failure Modes', result.skill_markdown)
        self.assertIn('## References', result.skill_markdown)
        self.assertIn('references/evidence.md', result.skill_markdown)
        self.assertIn('references/examples.md', result.skill_markdown)
        self.assertIn('Use when', result.description)

    def test_renderer_splits_long_content_into_references(self) -> None:
        renderer = PortableSkillRenderer()
        result = renderer.render(skill=self._build_skill(), graph=self._build_graph())
        evidence_ref = result.references['references/evidence.md']

        self.assertIn('Evidence References', evidence_ref)
        self.assertIn('Transcript Notes', evidence_ref)
        self.assertIn('OCR Notes', evidence_ref)
        self.assertIn('Keyframe Notes', evidence_ref)
        self.assertIn('ev-root', evidence_ref)
        self.assertIn('ev-1', evidence_ref)
        self.assertIn('ev-2', evidence_ref)
        self.assertIn('ev-3', evidence_ref)
        self.assertIn('ev-4', evidence_ref)

    def test_renderer_respects_line_limit(self) -> None:
        skill = self._build_skill()
        graph = self._build_graph()
        graph.steps.extend(
            [
                StepNode(step=3, action='Collect runbook diffs.', why='Track follow-up actions.', node_id='step-3'),
                StepNode(step=4, action='Draft reviewer packet summary.', why='Speed reviewer decision.', node_id='step-4'),
                StepNode(step=5, action='Record closure evidence.', why='Support auditability.', node_id='step-5'),
                StepNode(step=6, action='Archive trial loop output.', why='Prepare metrics ingestion.', node_id='step-6'),
            ]
        )
        renderer = PortableSkillRenderer(line_limit=24)
        result = renderer.render(skill=skill, graph=graph)

        self.assertEqual(result.line_limit, 24)
        self.assertLessEqual(result.line_count, 24)


if __name__ == '__main__':
    unittest.main()
