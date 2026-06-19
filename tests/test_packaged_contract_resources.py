from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omni_skill_pipeline.config import load_settings


REPO_ROOT = Path(__file__).resolve().parents[1]


class PackagedContractResourcesTests(unittest.TestCase):
    def test_packaged_contracts_match_published_contract_docs(self) -> None:
        package_contract_root = REPO_ROOT / "src" / "omni_skill_pipeline" / "resources" / "contracts"
        docs_contract_root = REPO_ROOT / "docs" / "latest" / "contracts"

        for filename in ["SKILL.template.md", "skill.schema.json"]:
            self.assertEqual(
                (package_contract_root / filename).read_text(encoding="utf-8"),
                (docs_contract_root / filename).read_text(encoding="utf-8"),
            )

    def test_load_settings_falls_back_to_packaged_contracts_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = load_settings(repo_root=Path(tmp_dir))

        self.assertTrue(settings.template_path.is_file())
        self.assertTrue(settings.schema_path.is_file())
        self.assertIn("resources", settings.template_path.as_posix())


if __name__ == "__main__":
    unittest.main()
