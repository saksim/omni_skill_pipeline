from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e11-perf-cost-baseline-manifest.json'
DEFAULT_OUTPUT_PATH = REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e11-perf-cost-baseline-report.json'


def _to_float(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, numeric)


def _to_int(value: Any) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = 0
    return max(0, numeric)


def _round(value: float) -> float:
    return round(float(value), 4)


def _ratio_increase(*, baseline: float, candidate: float) -> float:
    if baseline <= 0:
        return 0.0 if candidate <= 0 else 1.0
    return (candidate - baseline) / baseline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Compare fixed baseline samples across latency, token usage, and provider call counts.',
    )
    parser.add_argument(
        '--manifest',
        default=str(DEFAULT_MANIFEST_PATH),
        help='Performance/cost baseline manifest path.',
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


def _normalize_token_usage(payload: Any, *, sample_id: str, context: str) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError('%s sample %s is missing token_usage object.' % (context, sample_id))
    input_tokens = _to_int(payload.get('input_tokens', 0))
    output_tokens = _to_int(payload.get('output_tokens', 0))
    default_total = input_tokens + output_tokens
    total_tokens = _to_int(payload.get('total_tokens', default_total))
    if total_tokens < default_total:
        total_tokens = default_total
    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': total_tokens,
    }


def _normalize_provider_calls(payload: Any, *, sample_id: str, context: str) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError('%s sample %s is missing provider_calls object.' % (context, sample_id))
    normalized: dict[str, int] = {}
    for key, raw_value in payload.items():
        provider = str(key).strip()
        if not provider:
            continue
        normalized[provider] = _to_int(raw_value)
    return normalized


def _normalize_metrics(payload: Any, *, sample_id: str, context: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError('%s sample %s is missing metrics object.' % (context, sample_id))
    duration_ms = _to_float(payload.get('duration_ms', payload.get('elapsed_ms', 0.0)))
    token_usage = _normalize_token_usage(payload.get('token_usage'), sample_id=sample_id, context=context)
    provider_calls = _normalize_provider_calls(payload.get('provider_calls'), sample_id=sample_id, context=context)
    return {
        'duration_ms': duration_ms,
        'token_usage': token_usage,
        'provider_calls': provider_calls,
        'provider_calls_total': sum(provider_calls.values()),
    }


def _normalize_thresholds(payload: Any) -> dict[str, float | int]:
    data = payload if isinstance(payload, dict) else {}
    return {
        'max_duration_increase_ratio': max(0.0, _to_float(data.get('max_duration_increase_ratio', 0.2))),
        'max_token_increase_ratio': max(0.0, _to_float(data.get('max_token_increase_ratio', 0.15))),
        'max_provider_call_increase': _to_int(data.get('max_provider_call_increase', 2)),
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
    inline_candidate = payload.get('candidate_metrics', payload.get('candidate'))
    candidate_metrics = None
    if isinstance(inline_candidate, dict):
        candidate_metrics = _normalize_metrics(
            inline_candidate,
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
    return {
        'manifest_id': str(payload.get('manifest_id', '')).strip() or 'unknown',
        'manifest_version': str(payload.get('manifest_version', '')).strip() or 'unknown',
        'created_on': str(payload.get('created_on', '')).strip(),
        'description': str(payload.get('description', '')).strip(),
        'samples': [_normalize_manifest_sample(item) for item in samples_raw],
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


def _resolve_candidate_metrics(sample: dict[str, Any], *, candidate_map: dict[str, dict[str, Any]] | None) -> dict[str, Any]:
    sample_id = sample['sample_id']
    if candidate_map is not None and sample_id in candidate_map:
        return candidate_map[sample_id]
    inline = sample.get('candidate_metrics')
    if isinstance(inline, dict):
        return inline
    raise ValueError('Candidate metrics missing for sample %s.' % sample_id)


def _provider_call_deltas(baseline: dict[str, int], candidate: dict[str, int]) -> dict[str, int]:
    keys = set(baseline.keys()) | set(candidate.keys())
    deltas: dict[str, int] = {}
    for key in sorted(keys):
        deltas[key] = int(candidate.get(key, 0)) - int(baseline.get(key, 0))
    return deltas


def build_report(
    manifest: dict[str, Any],
    *,
    candidate_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    regressed_samples: list[str] = []
    baseline_durations: list[float] = []
    candidate_durations: list[float] = []
    baseline_tokens: list[float] = []
    candidate_tokens: list[float] = []
    baseline_provider_calls: list[float] = []
    candidate_provider_calls: list[float] = []

    for sample in manifest['samples']:
        sample_id = sample['sample_id']
        baseline = sample['baseline_metrics']
        candidate = _resolve_candidate_metrics(sample, candidate_map=candidate_map)
        thresholds = sample['thresholds']

        baseline_duration = float(baseline['duration_ms'])
        candidate_duration = float(candidate['duration_ms'])
        baseline_total_tokens = int(baseline['token_usage']['total_tokens'])
        candidate_total_tokens = int(candidate['token_usage']['total_tokens'])
        baseline_calls_total = int(baseline['provider_calls_total'])
        candidate_calls_total = int(candidate['provider_calls_total'])

        duration_ratio = _round(
            _ratio_increase(baseline=baseline_duration, candidate=candidate_duration)
        )
        token_ratio = _round(
            _ratio_increase(baseline=float(baseline_total_tokens), candidate=float(candidate_total_tokens))
        )
        provider_call_increase = int(candidate_calls_total - baseline_calls_total)

        duration_regressed = duration_ratio > float(thresholds['max_duration_increase_ratio'])
        token_regressed = token_ratio > float(thresholds['max_token_increase_ratio'])
        provider_call_regressed = provider_call_increase > int(thresholds['max_provider_call_increase'])
        regressed = duration_regressed or token_regressed or provider_call_regressed
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
                    'duration_ms': _round(candidate_duration - baseline_duration),
                    'duration_increase_ratio': duration_ratio,
                    'token_total': int(candidate_total_tokens - baseline_total_tokens),
                    'token_increase_ratio': token_ratio,
                    'provider_calls_total': provider_call_increase,
                    'provider_calls_by_provider': _provider_call_deltas(
                        baseline['provider_calls'],
                        candidate['provider_calls'],
                    ),
                },
                'regression': {
                    'duration': duration_regressed,
                    'token': token_regressed,
                    'provider_calls': provider_call_regressed,
                },
                'status': 'regressed' if regressed else 'pass',
                'notes': sample.get('notes', ''),
            }
        )

        baseline_durations.append(baseline_duration)
        candidate_durations.append(candidate_duration)
        baseline_tokens.append(float(baseline_total_tokens))
        candidate_tokens.append(float(candidate_total_tokens))
        baseline_provider_calls.append(float(baseline_calls_total))
        candidate_provider_calls.append(float(candidate_calls_total))

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
        'compared_metrics': ['duration_ms', 'token_usage.total_tokens', 'provider_calls_total'],
        'averages': {
            'baseline_duration_ms': _round(mean(baseline_durations)) if baseline_durations else 0.0,
            'candidate_duration_ms': _round(mean(candidate_durations)) if candidate_durations else 0.0,
            'baseline_total_tokens': _round(mean(baseline_tokens)) if baseline_tokens else 0.0,
            'candidate_total_tokens': _round(mean(candidate_tokens)) if candidate_tokens else 0.0,
            'baseline_provider_calls_total': _round(mean(baseline_provider_calls)) if baseline_provider_calls else 0.0,
            'candidate_provider_calls_total': _round(mean(candidate_provider_calls)) if candidate_provider_calls else 0.0,
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
        print('Perf-cost baseline failed: %s' % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_report(output_path, report)
        print('Perf-cost baseline report written: %s' % output_path)

    print(
        'Perf-cost baseline samples=%s pass=%s regressed=%s'
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
