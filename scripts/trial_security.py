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

from omni_skill_pipeline.validation import evaluate_trial_security_from_bundle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run CBT-13 trial security gate on a distillation bundle before package export.',
    )
    parser.add_argument(
        '--bundle',
        required=True,
        help='Path to distillation bundle JSON.',
    )
    parser.add_argument(
        '--output',
        default='-',
        help='Report output path (JSON). Use "-" for stdout.',
    )
    parser.add_argument(
        '--allow-sensitive-class',
        action='append',
        default=[],
        help='Approved sensitive class override. Repeat for multiple entries.',
    )
    return parser.parse_args()


def _write_output(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    args = _parse_args()
    approved_classes = {str(item).strip().lower() for item in args.allow_sensitive_class if str(item).strip()}
    try:
        report = evaluate_trial_security_from_bundle(
            bundle_path=Path(args.bundle),
            approved_sensitive_classes=approved_classes,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print('Trial security gate failed: %s' % exc, file=sys.stderr)
        return 2

    output_payload = {
        'validated_at_utc': datetime.now(timezone.utc).isoformat(),
        **report.to_dict(),
    }
    text = json.dumps(output_payload, ensure_ascii=False, indent=2)
    output_path = str(args.output).strip()
    if output_path == '-':
        print(text)
    else:
        resolved = Path(output_path).resolve()
        _write_output(resolved, output_payload)
        print('Trial security gate report written: %s' % resolved)

    if report.status != 'pass':
        print('Trial security gate failed. failure_codes=%s' % ','.join(report.failure_codes))
        return 2
    print('Trial security gate passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
