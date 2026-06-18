from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.feedback_loop import QualityFeedbackLoopBuilder, QualityFeedbackLoopConfig

DEFAULT_RUN_REPORT_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'controlled-trial' / 'controlled-trial-run-report.json'
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'quality-feedback-loop-report.json'
)
DEFAULT_SUMMARY_OUTPUT_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'quality-feedback-loop-summary.md'
)
DEFAULT_CALIBRATION_OUTPUT_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'quality-feedback-loop-calibration-manifest.json'
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build quality feedback loop artifacts from controlled-trial run report.',
    )
    parser.add_argument(
        '--run-report',
        default=str(DEFAULT_RUN_REPORT_PATH),
        help='Controlled-trial run report JSON path.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_OUTPUT_PATH),
        help='Quality feedback loop report output path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--summary-output',
        default=str(DEFAULT_SUMMARY_OUTPUT_PATH),
        help='Markdown summary output path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--calibration-output',
        default=str(DEFAULT_CALIBRATION_OUTPUT_PATH),
        help='Calibration manifest output path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--repeat-threshold',
        type=int,
        default=2,
        help='Minimum repeated defect sample count to emit regression cases.',
    )
    parser.add_argument(
        '--reviewer-edit-distance-threshold',
        type=float,
        default=25.0,
        help='Reviewer edit-distance threshold (percent) for high-edit regression signal.',
    )
    parser.add_argument('--print-json', action='store_true', help='Print full report JSON.')
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('Run report root must be a JSON object.')
    return payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def main() -> int:
    args = _parse_args()
    run_report_path = Path(args.run_report).resolve()
    try:
        run_report = _read_json(run_report_path)
        builder = QualityFeedbackLoopBuilder(
            QualityFeedbackLoopConfig(
                repeat_threshold=max(1, int(args.repeat_threshold)),
                reviewer_edit_distance_threshold=max(0.0, float(args.reviewer_edit_distance_threshold)),
            )
        )
        report = builder.build_from_run_report(run_report, base_dir=run_report_path.parent)
        summary_markdown = builder.render_summary_markdown(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print('Quality feedback loop failed: %s' % exc, file=sys.stderr)
        return 2

    output_value = str(args.output or '').strip()
    if output_value and output_value != '-':
        output_path = Path(output_value).resolve()
        _write_json(output_path, report)
        print('Quality feedback loop report written: %s' % output_path)

    calibration_value = str(args.calibration_output or '').strip()
    if calibration_value and calibration_value != '-':
        calibration_output_path = Path(calibration_value).resolve()
        calibration_payload = report.get('calibration_manifest', {})
        if isinstance(calibration_payload, dict):
            _write_json(calibration_output_path, calibration_payload)
            print('Calibration manifest written: %s' % calibration_output_path)

    summary_value = str(args.summary_output or '').strip()
    if summary_value and summary_value != '-':
        summary_path = Path(summary_value).resolve()
        _write_text(summary_path, summary_markdown)
        print('Quality feedback loop summary written: %s' % summary_path)

    summary = report.get('summary', {}) if isinstance(report, dict) else {}
    print(
        'Quality feedback loop samples=%s remediation_plans=%s regression_cases=%s calibration_samples=%s'
        % (
            str(summary.get('sample_count', 0)),
            str(summary.get('remediation_plan_count', 0)),
            str(summary.get('regression_case_count', 0)),
            str(summary.get('calibration_sample_count', 0)),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
