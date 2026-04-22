from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.heuristic_atom_extractor import HeuristicAtomExtractor
from omni_skill_pipeline.models import AtomType, ContentType, EvidenceNode, Modality


class ModalityAtomStrategyTests(unittest.TestCase):
    def test_audio_prioritizes_question_and_event_atoms(self) -> None:
        extractor = HeuristicAtomExtractor()
        question_node = EvidenceNode(
            asset_id='asset-audio',
            modality=Modality.AUDIO,
            content_type=ContentType.SPEECH,
            span_ref='video:timestamp:1.00-2.00',
            text_content='Can we rollback this release now?',
            tags=['utterance_act:question', 'speaker_role:oncall'],
            evidence_id='ev-audio-q',
        )
        decision_node = EvidenceNode(
            asset_id='asset-audio',
            modality=Modality.AUDIO,
            content_type=ContentType.SPEECH,
            span_ref='video:timestamp:2.00-3.00',
            text_content='Decision: rollback approved and action item assigned.',
            tags=['utterance_act:decision', 'speaker_role:manager'],
            evidence_id='ev-audio-d',
        )

        atoms = extractor.extract([question_node, decision_node])
        atom_types = {item.atom_type for item in atoms}
        self.assertIn(AtomType.QUESTION, atom_types)
        self.assertIn(AtomType.EVENT, atom_types)

    def test_video_prioritizes_event_atom(self) -> None:
        extractor = HeuristicAtomExtractor()
        video_node = EvidenceNode(
            asset_id='asset-video',
            modality=Modality.VIDEO,
            content_type=ContentType.EVENT,
            span_ref='frame:0003@8.00s:event',
            text_content='Operator clicked rollback and dismissed deploy dialog.',
            tags=['block:frame_event'],
            evidence_id='ev-video-event',
        )
        atoms = extractor.extract([video_node])

        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0].atom_type, AtomType.EVENT)
        self.assertEqual(atoms[0].attributes.get('heuristic_rule'), 'video_event_span')

    def test_tabular_prioritizes_metric_guardrail_atom(self) -> None:
        extractor = HeuristicAtomExtractor()
        metric_node = EvidenceNode(
            asset_id='asset-tabular',
            modality=Modality.TABULAR,
            content_type=ContentType.METRIC,
            span_ref='timeseries:metric:0001',
            text_content=(
                'baseline_mean=101.2 baseline_std=1.7 '
                'drift_label=upward_drift drift_score=2.4 change_points=2026-04-22T01:00:00'
            ),
            tags=['timeseries', 'latency_ms'],
            evidence_id='ev-ts-metric',
        )
        atoms = extractor.extract([metric_node])

        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0].atom_type, AtomType.METRIC_GUARDRAIL)
        self.assertEqual(atoms[0].attributes.get('heuristic_rule'), 'tabular_guardrail_regex')


if __name__ == "__main__":
    unittest.main()
