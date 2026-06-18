from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CALIBRATION_MANIFEST = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-manifest.json'
)
DEFAULT_CALIBRATION_REPORT_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-report.json'
)
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-calibration-ga-validation-plan.json'
)
DEFAULT_STAGES = (
    'calibration_contract',
    'review_policy_contract',
    'calibration_report',
)
ALL_STAGES = tuple(DEFAULT_STAGES)


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print a calibration GA-hardening validation command pack for Linux.',
    )
    parser.add_argument(
        '--python',
        default='python3',
        help='Python command for Linux execution, e.g. "python3" or "python3.11".',
    )
    parser.add_argument(
        '--stages',
        nargs='*',
        choices=ALL_STAGES,
        default=list(DEFAULT_STAGES),
        help='Validation stages to include. Defaults to full calibration GA command pack.',
    )
    parser.add_argument(
        '--manifest',
        default=str(DEFAULT_CALIBRATION_MANIFEST),
        help='Calibration manifest path forwarded to scripts/tune_review.py.',
    )
    parser.add_argument(
        '--calibration-report-output',
        default=str(DEFAULT_CALIBRATION_REPORT_OUTPUT),
        help='Calibration report output path forwarded to scripts/tune_review.py.',
    )
    parser.add_argument(
        '--margin',
        type=float,
        default=0.03,
        help='Margin forwarded to scripts/tune_review.py.',
    )
    parser.add_argument(
        '--fail-on-mismatch',
        action='store_true',
        help='Forward --fail-on-mismatch to scripts/tune_review.py.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command pack only without running commands.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_PLAN_OUTPUT),
        help='Write JSON plan/report to this path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print JSON plan/report to stdout.',
    )
    return parser.parse_args()


def _split_python_command(raw: str) -> list[str]:
    parts = shlex.split(raw, posix=os.name != 'nt')
    if not parts:
        raise ValueError('Empty --python command.')
    return parts


def _build_stage_map(args: argparse.Namespace, *, python_cmd: list[str]) -> dict[str, StageSpec]:
    manifest_path = str(Path(args.manifest).resolve())
    calibration_report_output = str(Path(args.calibration_report_output).resolve())
    calibration_report_command = [
        *python_cmd,
        'scripts/tune_review.py',
        '--manifest',
        manifest_path,
        '--margin',
        str(float(args.margin)),
        '--output',
        calibration_report_output,
    ]
    if args.fail_on_mismatch:
        calibration_report_command.append('--fail-on-mismatch')

    return {
        'calibration_contract': StageSpec(
            name='calibration_contract',
            description='Validate calibration manifest contract checks in tune_review_policy script tests.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_tune_review_policy.TuneReviewPolicyScriptTests.test_script_rejects_invalid_manifest',
            ],
        ),
        'review_policy_contract': StageSpec(
            name='review_policy_contract',
            description='Validate review policy threshold decision contract tests.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_review_policy.ReviewPolicyTests',
            ],
        ),
        'calibration_report': StageSpec(
            name='calibration_report',
            description='Generate calibration report from labeled manifest using tune_review_policy script.',
            command=calibration_report_command,
        ),
    }


def _build_plan(
    stage_specs: list[StageSpec],
    *,
    calibration_manifest: str,
    calibration_report_output: str,
    margin: float,
    fail_on_mismatch: bool,
) -> dict[str, Any]:
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'stage_count': len(stage_specs),
        'calibration_manifest': calibration_manifest,
        'calibration_report_output': calibration_report_output,
        'margin': float(margin),
        'fail_on_mismatch': bool(fail_on_mismatch),
        'stages': [
            {
                'name': stage.name,
                'description': stage.description,
                'command': stage.command,
            }
            for stage in stage_specs
        ],
    }


def _print_plan(stage_specs: list[StageSpec]) -> None:
    print('Selected stages: %s' % ', '.join(stage.name for stage in stage_specs))
    for stage in stage_specs:
        print('Stage: %s' % stage.name)
        print('Description: %s' % stage.description)
        print('Command: %s' % ' '.join(stage.command))


def _write_plan(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _run_stages(stage_specs: list[StageSpec]) -> int:
    for stage in stage_specs:
        print('Running stage: %s' % stage.name)
        completed = subprocess.run(stage.command, check=False)
        if completed.returncode != 0:
            print(
                'Stage failed: %s (exit=%s)' % (stage.name, completed.returncode),
                file=sys.stderr,
            )
            return completed.returncode
    return 0


def main() -> int:
    args = _parse_args()
    if not args.stages:
        print('No stages selected. Use --stages with at least one value.', file=sys.stderr)
        return 2

    try:
        python_cmd = _split_python_command(args.python)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stage_map = _build_stage_map(args, python_cmd=python_cmd)
    stage_specs = [stage_map[name] for name in args.stages]
    _print_plan(stage_specs)

    plan_payload = _build_plan(
        stage_specs,
        calibration_manifest=str(Path(args.manifest).resolve()),
        calibration_report_output=str(Path(args.calibration_report_output).resolve()),
        margin=float(args.margin),
        fail_on_mismatch=bool(args.fail_on_mismatch),
    )
    output_value = str(args.output or '').strip()
    if output_value and output_value != '-':
        output_path = Path(output_value).resolve()
        _write_plan(output_path, plan_payload)
        print('Plan written: %s' % output_path)

    if args.print_json:
        print(json.dumps(plan_payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0
    return _run_stages(stage_specs)


if __name__ == '__main__':
    raise SystemExit(main())
