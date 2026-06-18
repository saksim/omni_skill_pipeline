from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e11-quality-regression-manifest.json'
DEFAULT_OUTPUT_PATH = REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e11-quality-regression-report.json'


def _clamp_rate(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


def _to_int(value: Any) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = 0
    return max(0, numeric)


def _round(value: float) -> float:
    return round(float(value), 4)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Compare fixed baseline samples across traceability and reviewer edit distance.',
    )
    parser.add_argument(
        '--manifest',
        default=str(DEFAULT_MANIFEST_PATH),
        help='Baseline manifest path.',
    )
    parser.add_argument(
        '--candidate',
        default='',
        help='Candidate metrics JSON path. When empty, use candidate_metrics inside manifest samples.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_OUTPUT_PATH),
        help='Output report JSON path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print full report JSON to stdout.',
    )
    parser.add_argument(
        '--fail-on-regression',
        action='store_true',
        help='Exit with code 1 when any sample regresses.',
    )
    return parser.parse_args()


def _normalize_edit_distance(payload: Any, *, sample_id: str, context: str) -> dict[str, int | bool]:
    if not isinstance(payload, dict):
        raise ValueError('%s sample %s is missing reviewer_edit_distance object.' % (context, sample_id))
    step_edits = _to_int(payload.get('step_edits'))
    rule_edits = _to_int(payload.get('rule_edits'))
    verification_edits = _to_int(payload.get('verification_edits'))
    summary_rewritten = bool(payload.get('summary_rewritten', False))
    total_edits = step_edits + rule_edits + verification_edits + (1 if summary_rewritten else 0)
    return {
        'step_edits': step_edits,
        'rule_edits': rule_edits,
        'verification_edits': verification_edits,
        'summary_rewritten': summary_rewritten,
        'total_edits': total_edits,
    }


def _normalize_metrics(payload: Any, *, sample_id: str, context: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError('%s sample %s is missing metrics object.' % (context, sample_id))
    traceability = _clamp_rate(payload.get('traceability_rate', payload.get('traceability_score')))
    edit_distance = _normalize_edit_distance(
        payload.get('reviewer_edit_distance'),
        sample_id=sample_id,
        context=context,
    )
    return {
        'traceability_rate': traceability,
        'reviewer_edit_distance': edit_distance,
    }


def _normalize_thresholds(payload: Any) -> dict[str, float | int]:
    data = payload if isinstance(payload, dict) else {}
    max_traceability_drop = _clamp_rate(data.get('max_traceability_drop', 0.05))
    max_reviewer_edit_increase = _to_int(data.get('max_reviewer_edit_increase', 2))
    return {
        'max_traceability_drop': max_traceability_drop,
        'max_reviewer_edit_increase': max_reviewer_edit_increase,
    }


def _normalize_manifest_sample(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError('Sample must be a JSON object.')
    sample_id = str(payload.get('sample_id', '')).strip()
    if not sample_id:
        raise ValueError('Sample is missing sample_id.')
    modality = str(payload.get('modality', '')).strip() or 'unknown'
    baseline_metrics = _normalize_metrics(
        payload.get('baseline_metrics', payload.get('baseline')),
        sample_id=sample_id,
        context='manifest baseline',
    )
    inline_candidate_metrics = payload.get('candidate_metrics', payload.get('candidate'))
    candidate_metrics = None
    if isinstance(inline_candidate_metrics, dict):
        candidate_metrics = _normalize_metrics(
            inline_candidate_metrics,
            sample_id=sample_id,
            context='manifest candidate',
        )
    return {
        'sample_id': sample_id,
        'modality': modality,
        'baseline_metrics': baseline_metrics,
        'candidate_metrics': candidate_metrics,
        'thresholds': _normalize_thresholds(payload.get('thresholds')),
        'notes': str(payload.get('notes', '')).strip(),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('Manifest root must be a JSON object.')
    samples_raw = payload.get('samples')
    if not isinstance(samples_raw, list) or not samples_raw:
        raise ValueError('Manifest requires non-empty samples list.')
    samples = [_normalize_manifest_sample(item) for item in samples_raw]
    return {
        'manifest_id': str(payload.get('manifest_id', '')).strip() or 'unknown',
        'manifest_version': str(payload.get('manifest_version', '')).strip() or 'unknown',
        'created_on': str(payload.get('created_on', '')).strip(),
        'description': str(payload.get('description', '')).strip(),
        'samples': samples,
    }


def _load_candidate_map(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('Candidate root must be a JSON object.')
    samples_raw = payload.get('samples')
    if not isinstance(samples_raw, list) or not samples_raw:
        raise ValueError('Candidate file requires non-empty samples list.')
    candidate_map: dict[str, dict[str, Any]] = {}
    for item in samples_raw:
        if not isinstance(item, dict):
            raise ValueError('Candidate sample must be a JSON object.')
        sample_id = str(item.get('sample_id', '')).strip()
        if not sample_id:
            raise ValueError('Candidate sample is missing sample_id.')
        metrics_source = item.get('metrics', item)
        candidate_map[sample_id] = _normalize_metrics(
            metrics_source,
            sample_id=sample_id,
            context='candidate file',
        )
    return candidate_map


def _resolve_candidate_metrics(
    sample: dict[str, Any],
    *,
    candidate_map: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    sample_id = sample['sample_id']
    if candidate_map is not None and sample_id in candidate_map:
        return candidate_map[sample_id]
    inline = sample.get('candidate_metrics')
    if isinstance(inline, dict):
        return inline
    raise ValueError('Candidate metrics missing for sample %s.' % sample_id)


def build_report(
    manifest: dict[str, Any],
    *,
    candidate_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    regressed_samples: list[str] = []
    baseline_traceabilities: list[float] = []
    candidate_traceabilities: list[float] = []
    baseline_edit_totals: list[float] = []
    candidate_edit_totals: list[float] = []

    for sample in manifest['samples']:
        sample_id = sample['sample_id']
        baseline = sample['baseline_metrics']
        candidate = _resolve_candidate_metrics(sample, candidate_map=candidate_map)
        thresholds = sample['thresholds']

        baseline_traceability = float(baseline['traceability_rate'])
        candidate_traceability = float(candidate['traceability_rate'])
        baseline_edit_total = int(baseline['reviewer_edit_distance']['total_edits'])
        candidate_edit_total = int(candidate['reviewer_edit_distance']['total_edits'])

        traceability_delta = _round(candidate_traceability - baseline_traceability)
        reviewer_edit_delta = int(candidate_edit_total - baseline_edit_total)

        traceability_regressed = traceability_delta < (-1.0 * float(thresholds['max_traceability_drop']))
        reviewer_edit_regressed = reviewer_edit_delta > int(thresholds['max_reviewer_edit_increase'])
        regressed = traceability_regressed or reviewer_edit_regressed
        if regressed:
            regressed_samples.append(sample_id)

        comparisons.append(
            {
                'sample_id': sample_id,
                'modality': sample['modality'],
                'baseline_metrics': baseline,
                'candidate_metrics': candidate,
                'thresholds': thresholds,
                'delta': {
                    'traceability_rate': traceability_delta,
                    'reviewer_edit_distance_total': reviewer_edit_delta,
                },
                'regression': {
                    'traceability': traceability_regressed,
                    'reviewer_edit_distance': reviewer_edit_regressed,
                },
                'status': 'regressed' if regressed else 'pass',
                'notes': sample.get('notes', ''),
            }
        )

        baseline_traceabilities.append(baseline_traceability)
        candidate_traceabilities.append(candidate_traceability)
        baseline_edit_totals.append(float(baseline_edit_total))
        candidate_edit_totals.append(float(candidate_edit_total))

    sample_count = len(comparisons)
    regressed_count = len(regressed_samples)
    pass_count = sample_count - regressed_count
    return {
        'manifest_id': manifest['manifest_id'],
        'manifest_version': manifest['manifest_version'],
        'sample_count': sample_count,
        'pass_count': pass_count,
        'regressed_count': regressed_count,
        'regressed_samples': regressed_samples,
        'compared_metrics': ['traceability_rate', 'reviewer_edit_distance'],
        'averages': {
            'baseline_traceability_rate': _round(mean(baseline_traceabilities)) if baseline_traceabilities else 0.0,
            'candidate_traceability_rate': _round(mean(candidate_traceabilities)) if candidate_traceabilities else 0.0,
            'baseline_reviewer_edit_distance_total': _round(mean(baseline_edit_totals)) if baseline_edit_totals else 0.0,
            'candidate_reviewer_edit_distance_total': _round(mean(candidate_edit_totals)) if candidate_edit_totals else 0.0,
        },
        'samples': comparisons,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest).resolve()
    candidate_path = Path(args.candidate).resolve() if str(args.candidate).strip() else None
    output_path = None if str(args.output).strip() == '-' else Path(args.output).resolve()
    try:
        manifest = load_manifest(manifest_path)
        candidate_map = _load_candidate_map(candidate_path) if candidate_path is not None else None
        report = build_report(manifest, candidate_map=candidate_map)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print('Quality regression failed: %s' % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_report(output_path, report)
        print('Quality regression report written: %s' % output_path)

    print(
        'Quality regression samples=%s pass=%s regressed=%s'
        % (report['sample_count'], report['pass_count'], report['regressed_count'])
    )
    if report['regressed_samples']:
        print('Regressed samples: %s' % ', '.join(report['regressed_samples']))
    else:
        print('Regressed samples: none')

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.fail_on_regression and report['regressed_count'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
