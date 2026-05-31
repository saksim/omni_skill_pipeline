from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = (
    REPO_ROOT
    / 'docs'
    / 'current'
    / 'status'
    / 'baselines'
    / 'trial-manifests'
    / 'trial-sample-manifest.template.json'
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / 'docs'
    / 'current'
    / 'status'
    / 'baselines'
    / 'trial-manifests'
    / 'trial-sample-manifest-validation-report.json'
)

SUPPORTED_MODALITIES = {
    'text',
    'audio',
    'image',
    'video',
    'tabular',
    'mixed_corpus',
}
SUPPORTED_SENSITIVITY_LEVELS = {
    'public',
    'internal',
    'confidential',
    'restricted',
}
SUPPORTED_TARGET_PACKAGE_FORMATS = {
    'codex',
    'claude-code',
    'opencode',
    'portable',
    'all',
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate controlled-trial sample manifest contracts.',
    )
    parser.add_argument(
        '--manifest',
        default=str(DEFAULT_MANIFEST_PATH),
        help='Trial sample manifest path.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_OUTPUT_PATH),
        help='Output report path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print full report JSON.',
    )
    return parser.parse_args()


def _as_non_empty_string(value: Any) -> str:
    if not isinstance(value, str):
        return ''
    return value.strip()


def _validate_asset(*, sample_index: int, asset_index: int, payload: Any) -> list[str]:
    errors: list[str] = []
    label = 'samples[%s].asset_list[%s]' % (sample_index, asset_index)
    if not isinstance(payload, dict):
        return ['%s must be an object with asset_id, asset_type, and uri.' % label]

    for field_name in ('asset_id', 'asset_type', 'uri'):
        value = _as_non_empty_string(payload.get(field_name))
        if not value:
            errors.append('%s.%s is required and must be a non-empty string.' % (label, field_name))
    return errors


def _validate_sample(sample: Any, *, index: int) -> list[str]:
    errors: list[str] = []
    label = 'samples[%s]' % index
    if not isinstance(sample, dict):
        return ['%s must be an object.' % label]

    required_string_fields = (
        'sample_id',
        'modality',
        'scenario',
        'source_owner',
        'sensitivity',
        'review_owner',
        'target_package_format',
        'expected_output_type',
    )
    values: dict[str, str] = {}
    for field_name in required_string_fields:
        value = _as_non_empty_string(sample.get(field_name))
        values[field_name] = value
        if not value:
            errors.append('%s.%s is required and must be a non-empty string.' % (label, field_name))

    modality = values.get('modality', '')
    if modality and modality not in SUPPORTED_MODALITIES:
        errors.append(
            '%s.modality "%s" is unsupported. Allowed values: %s.'
            % (label, modality, ', '.join(sorted(SUPPORTED_MODALITIES)))
        )

    sensitivity = values.get('sensitivity', '')
    if sensitivity and sensitivity not in SUPPORTED_SENSITIVITY_LEVELS:
        errors.append(
            '%s.sensitivity "%s" is unsupported. Allowed values: %s.'
            % (label, sensitivity, ', '.join(sorted(SUPPORTED_SENSITIVITY_LEVELS)))
        )

    target_package_format = values.get('target_package_format', '')
    if target_package_format and target_package_format not in SUPPORTED_TARGET_PACKAGE_FORMATS:
        errors.append(
            '%s.target_package_format "%s" is unsupported. Allowed values: %s.'
            % (
                label,
                target_package_format,
                ', '.join(sorted(SUPPORTED_TARGET_PACKAGE_FORMATS)),
            )
        )

    asset_list = sample.get('asset_list')
    if not isinstance(asset_list, list) or not asset_list:
        errors.append('%s.asset_list must be a non-empty list of assets.' % label)
    else:
        for asset_index, asset in enumerate(asset_list):
            errors.extend(_validate_asset(sample_index=index, asset_index=asset_index, payload=asset))
    return errors


def validate_manifest(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ['Manifest root must be a JSON object.']

    required_root_string_fields = ('manifest_id', 'manifest_version')
    for field_name in required_root_string_fields:
        value = _as_non_empty_string(payload.get(field_name))
        if not value:
            errors.append('%s is required and must be a non-empty string.' % field_name)

    samples = payload.get('samples')
    if not isinstance(samples, list) or not samples:
        errors.append('samples must be a non-empty list.')
        return errors

    for index, sample in enumerate(samples):
        errors.extend(_validate_sample(sample, index=index))
    return errors


def _build_report(*, manifest_path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        'validated_at_utc': datetime.now(timezone.utc).isoformat(),
        'manifest_path': str(manifest_path),
        'error_count': len(errors),
        'status': 'pass' if not errors else 'fail',
        'errors': errors,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest).resolve()
    output_path = None if str(args.output).strip() == '-' else Path(args.output).resolve()

    try:
        payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print('Trial manifest validation failed: unable to read manifest: %s' % exc, file=sys.stderr)
        return 2

    errors = validate_manifest(payload)
    report = _build_report(manifest_path=manifest_path, errors=errors)
    if output_path is not None:
        _write_report(output_path, report)
        print('Trial manifest validation report written: %s' % output_path)

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if errors:
        print('Trial manifest validation failed with %s error(s):' % len(errors), file=sys.stderr)
        for item in errors:
            print('- %s' % item, file=sys.stderr)
        return 2

    print('Trial manifest validation passed. samples=%s' % len(payload.get('samples', [])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
