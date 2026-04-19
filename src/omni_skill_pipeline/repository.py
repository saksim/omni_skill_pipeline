from __future__ import annotations

from pathlib import Path
from typing import Dict

from omni_skill_pipeline.models import DistillBundle
from omni_skill_pipeline.utils import slugify


class FileArtifactRepository(object):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bundle(self, bundle: DistillBundle) -> Dict[str, str]:
        slug = slugify(bundle.skill.name)
        bundle_dir = self.base_dir / ("%s-%s" % (slug, bundle.skill.skill_id[:8]))
        bundle_dir.mkdir(parents=True, exist_ok=True)

        artifacts = {
            "asset": bundle_dir / "asset.json",
            "evidence": bundle_dir / "evidence.json",
            "insights": bundle_dir / "insights.json",
            "skill": bundle_dir / "skill.json",
            "skill_markdown": bundle_dir / "SKILL.md",
            "bundle": bundle_dir / "bundle.json",
        }

        artifacts["asset"].write_text(bundle.asset.to_json() + "\n", encoding="utf-8")
        artifacts["evidence"].write_text(
            "[\n%s\n]\n" % ",\n".join(unit.to_json() for unit in bundle.evidence_units),
            encoding="utf-8",
        )
        artifacts["insights"].write_text(
            "[\n%s\n]\n" % ",\n".join(insight.to_json() for insight in bundle.insights),
            encoding="utf-8",
        )
        artifacts["skill"].write_text(bundle.skill.to_json() + "\n", encoding="utf-8")
        artifacts["skill_markdown"].write_text(bundle.skill_markdown, encoding="utf-8")

        artifact_strings = {name: str(path) for name, path in artifacts.items()}
        bundle.artifacts = artifact_strings
        artifacts["bundle"].write_text(bundle.to_json() + "\n", encoding="utf-8")
        return artifact_strings

