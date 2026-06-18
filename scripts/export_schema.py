from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))

    from omni_skill_pipeline.schema import SKILL_SCHEMA  # pylint: disable=import-outside-toplevel

    target = repo_root / "docs" / "latest" / "contracts" / "skill.schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(SKILL_SCHEMA, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
