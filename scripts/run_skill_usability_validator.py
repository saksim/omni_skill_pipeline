from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.validation import validate_skill_package


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate exported skill package usability and safety constraints.',
    )
    parser.add_argument(
        '--package',
        required=True,
        help='Path to exported package directory containing SKILL.md.',
    )
    parser.add_argument(
        '--output',
        default='-',
        help='Validation report output path (JSON). Use "-" for stdout only.',
    )
    parser.add_argument(
        '--max-lines',
        type=int,
        default=500,
        help='Max allowed SKILL.md line count.',
    )
    parser.add_argument(
        '--min-description-words',
        type=int,
        default=8,
        help='Min words required in frontmatter description.',
    )
    parser.add_argument(
        '--max-description-words',
        type=int,
        default=80,
        help='Max words allowed in frontmatter description.',
    )
    return parser.parse_args()


def _write_output(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    args = _parse_args()
    report = validate_skill_package(
        package_path=Path(args.package),
        max_lines=int(args.max_lines),
        min_description_words=int(args.min_description_words),
        max_description_words=int(args.max_description_words),
    )
    output_payload = {
        'validated_at_utc': datetime.now(timezone.utc).isoformat(),
        **report.to_dict(),
    }
    text = json.dumps(output_payload, ensure_ascii=False, indent=2)
    if str(args.output).strip() == '-':
        print(text)
    else:
        output_path = Path(args.output).resolve()
        _write_output(output_path, output_payload)
        print('Skill usability validation report written: %s' % output_path)

    if report.status != 'pass':
        print('Skill usability validation failed. failure_codes=%s' % ','.join(report.failure_codes))
        return 2

    print('Skill usability validation passed. lines=%s' % report.actual_line_count)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
