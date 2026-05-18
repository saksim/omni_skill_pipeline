from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.heuristic_atom_extractor import HeuristicAtomExtractor
from omni_skill_pipeline.interfaces import AtomExtractor
from omni_skill_pipeline.models import AtomType, ContentType, EvidenceNode, Modality


class HeuristicAtomExtractorTests(unittest.TestCase):
    def test_extractor_is_atom_extractor_protocol_compatible(self) -> None:
        extractor = HeuristicAtomExtractor()
        self.assertTrue(isinstance(extractor, AtomExtractor))

    def test_extractor_emits_procedure_rule_verification_and_anti_pattern(self) -> None:
        extractor = HeuristicAtomExtractor()
        nodes = [
            EvidenceNode(
                asset_id='asset-a',
                modality=Modality.TEXT,
                content_type=ContentType.TEXT,
                span_ref='line:0001',
                text_content=(
                    "1. Capture baseline latency before deploy.\n"
                    "If error rate exceeds 5%, rollback immediately.\n"
                    "Verify p95 latency returns below 200ms.\n"
                    "Avoid adding indexes without EXPLAIN validation."
                ),
                evidence_id='ev-001',
            )
        ]

        atoms = extractor.extract(nodes)
        atom_types = {item.atom_type for item in atoms}

        self.assertIn(AtomType.PROCEDURE, atom_types)
        self.assertIn(AtomType.RULE, atom_types)
        self.assertIn(AtomType.VERIFICATION, atom_types)
        self.assertIn(AtomType.ANTI_PATTERN, atom_types)
        self.assertTrue(all(item.evidence_refs == ['ev-001'] for item in atoms))
        self.assertTrue(all(item.attributes.get('source_span_ref') == 'line:0001' for item in atoms))

    def test_extractor_fallbacks_to_claim_when_no_pattern_matches(self) -> None:
        extractor = HeuristicAtomExtractor()
        nodes = [
            EvidenceNode(
                asset_id='asset-b',
                modality=Modality.IMAGE,
                content_type=ContentType.SCENE,
                span_ref='image:scene:0001',
                text_content='Dashboard snapshot for weekly report.',
                evidence_id='ev-002',
            )
        ]

        atoms = extractor.extract(nodes)
        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0].atom_type, AtomType.CLAIM)
        self.assertEqual(atoms[0].evidence_refs, ['ev-002'])
        self.assertEqual(atoms[0].attributes.get('heuristic_rule'), 'fallback_claim')


if __name__ == "__main__":
    unittest.main()
