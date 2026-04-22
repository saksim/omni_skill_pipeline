from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import AtomType
from omni_skill_pipeline.providers.openai_provider import OpenAILLMAtomEnhancer


class OpenAIAtomEnhancerTests(unittest.TestCase):
    def test_coerce_atom_type_defaults_to_claim_for_unknown_value(self) -> None:
        enhancer = object.__new__(OpenAILLMAtomEnhancer)
        self.assertEqual(enhancer._coerce_atom_type('event'), AtomType.EVENT)
        self.assertEqual(enhancer._coerce_atom_type('unknown-type'), AtomType.CLAIM)

    def test_sanitize_evidence_refs_filters_unknown_and_dedupes(self) -> None:
        enhancer = object.__new__(OpenAILLMAtomEnhancer)
        refs = enhancer._sanitize_evidence_refs(['ev-1', 'ev-2', 'ev-2', 'ev-x', ''], {'ev-1', 'ev-2'})
        self.assertEqual(refs, ['ev-1', 'ev-2'])


if __name__ == "__main__":
    unittest.main()
