from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.exceptions import ProviderExecutionError
from omni_skill_pipeline.extraction.llm_atom_extractor import LLMAtomExtractor
from omni_skill_pipeline.interfaces import AtomExtractor
from omni_skill_pipeline.models import AtomType, ContentType, EvidenceNode, Modality, SemanticAtom


class _StubBaseExtractor(object):
    def extract(self, evidence_nodes):
        return [
            SemanticAtom(
                atom_type=AtomType.PROCEDURE,
                summary='Capture baseline latency.',
                evidence_refs=['ev-1'],
                confidence=0.82,
            )
        ]


class _FailingEnhancer(object):
    def extract_atoms(self, evidence_nodes, *, seed_atoms=None):
        raise ProviderExecutionError('simulated llm failure')


class _SuccessfulEnhancer(object):
    def extract_atoms(self, evidence_nodes, *, seed_atoms=None):
        return [
            SemanticAtom(
                atom_type=AtomType.PROCEDURE,
                summary='Capture baseline latency.',
                evidence_refs=['ev-1'],
                confidence=0.6,
            ),
            SemanticAtom(
                atom_type=AtomType.EVENT,
                summary='Rollback executed after threshold breach.',
                evidence_refs=['ev-2'],
                confidence=0.77,
                attributes={'llm_enhanced': True},
            ),
            SemanticAtom(
                atom_type=AtomType.RULE,
                summary='If error rate > 5%, rollback within 5 minutes.',
                evidence_refs=['ev-2', 'ev-2'],
                confidence=0.8,
            ),
        ]


class LLMAtomExtractorTests(unittest.TestCase):
    def test_extractor_is_atom_extractor_protocol_compatible(self) -> None:
        extractor = LLMAtomExtractor(base_extractor=_StubBaseExtractor())
        self.assertTrue(isinstance(extractor, AtomExtractor))

    def test_fallback_to_base_atoms_when_llm_fails(self) -> None:
        extractor = LLMAtomExtractor(base_extractor=_StubBaseExtractor(), llm_enhancer=_FailingEnhancer())
        nodes = [
            EvidenceNode(
                asset_id='asset-a',
                modality=Modality.VIDEO,
                content_type=ContentType.EVENT,
                span_ref='frame:0001@1.00s:event',
                text_content='Rollback initiated.',
                evidence_id='ev-1',
            )
        ]
        atoms = extractor.extract(nodes)
        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0].atom_type, AtomType.PROCEDURE)
        self.assertEqual(atoms[0].summary, 'Capture baseline latency.')

    def test_merge_llm_atoms_without_overwriting_base_truth(self) -> None:
        extractor = LLMAtomExtractor(base_extractor=_StubBaseExtractor(), llm_enhancer=_SuccessfulEnhancer())
        nodes = [
            EvidenceNode(
                asset_id='asset-b',
                modality=Modality.AUDIO,
                content_type=ContentType.SPEECH,
                span_ref='video:timestamp:1.0-2.0',
                text_content='Rollback executed and threshold exceeded.',
                evidence_id='ev-2',
            )
        ]
        atoms = extractor.extract(nodes)
        atom_types = [item.atom_type for item in atoms]
        self.assertEqual(len(atoms), 3)
        self.assertEqual(atom_types[0], AtomType.PROCEDURE)
        self.assertIn(AtomType.EVENT, atom_types)
        self.assertIn(AtomType.RULE, atom_types)
        rule_atom = next(item for item in atoms if item.atom_type == AtomType.RULE)
        self.assertEqual(rule_atom.evidence_refs, ['ev-2'])


if __name__ == "__main__":
    unittest.main()
