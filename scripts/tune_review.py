from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.review_policy import ReviewPolicy, ReviewPolicyThresholds

DEFAULT_MANIFEST_PATH = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e7-calibration-manifest.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e7-calibration-report.json"
DECISIONS = ("auto_publish", "review_required", "reject")
SCORE_KEYS = (
    "traceability_score",
    "actionability_score",
    "coverage_score",
    "consistency_score",
    "noise_score",
    "novelty_score",
    "overall_score",
)


def _clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


def _round(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _coerce_scores(payload: dict[str, Any]) -> dict[str, float]:
    return {key: _clamp_score(payload.get(key, 0.0)) for key in SCORE_KEYS}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare quality scores against reviewer judgement and suggest threshold tuning.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Calibration dataset manifest JSON path.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Output report JSON path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.03,
        help="Margin used when generating threshold suggestions (default: %(default)s).",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print full report JSON to stdout.",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit with code 1 when policy decision differs from reviewer judgement.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object.")
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("Manifest requires non-empty 'samples'.")
    return payload


def _normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    sample_id = str(sample.get("sample_id", "")).strip()
    modality = str(sample.get("modality", "")).strip() or "unknown"
    quality_scores_raw = sample.get("quality_scores")
    reviewer_raw = sample.get("reviewer_judgement")
    if not sample_id:
        raise ValueError("Sample is missing sample_id.")
    if not isinstance(quality_scores_raw, dict):
        raise ValueError("Sample %s is missing quality_scores object." % sample_id)
    if not isinstance(reviewer_raw, dict):
        raise ValueError("Sample %s is missing reviewer_judgement object." % sample_id)
    reviewer_decision = str(reviewer_raw.get("decision", "")).strip()
    if reviewer_decision not in DECISIONS:
        raise ValueError("Sample %s reviewer_judgement.decision must be one of %s." % (sample_id, ", ".join(DECISIONS)))
    return {
        "sample_id": sample_id,
        "modality": modality,
        "quality_scores": _coerce_scores(quality_scores_raw),
        "reviewer_judgement": {
            "decision": reviewer_decision,
            "confidence": _clamp_score(reviewer_raw.get("confidence", 0.0)),
            "notes": str(reviewer_raw.get("notes", "")).strip(),
        },
    }


def _decision_confusion_matrix() -> dict[str, dict[str, int]]:
    return {reviewer: {policy: 0 for policy in DECISIONS} for reviewer in DECISIONS}


def _compare_samples(samples: list[dict[str, Any]], policy: ReviewPolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evaluations: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for sample in samples:
        policy_decision = policy.decide(sample["quality_scores"]).to_dict()
        reviewer_decision = sample["reviewer_judgement"]["decision"]
        matched = policy_decision["decision"] == reviewer_decision
        record = {
            "sample_id": sample["sample_id"],
            "modality": sample["modality"],
            "reviewer_decision": reviewer_decision,
            "policy_decision": policy_decision["decision"],
            "matched": matched,
            "policy_reason_codes": list(policy_decision.get("reason_codes", [])),
            "quality_scores": dict(sample["quality_scores"]),
            "reviewer_notes": sample["reviewer_judgement"]["notes"],
        }
        evaluations.append(record)
        if not matched:
            mismatches.append(record)
    return evaluations, mismatches


def _values_for_decision(samples: list[dict[str, Any]], decision: str, score_key: str) -> list[float]:
    values: list[float] = []
    for sample in samples:
        if sample["reviewer_judgement"]["decision"] != decision:
            continue
        values.append(float(sample["quality_scores"].get(score_key, 0.0)))
    return values


def _suggest_thresholds(
    *,
    samples: list[dict[str, Any]],
    current: ReviewPolicyThresholds,
    margin: float,
) -> dict[str, float]:
    safe_margin = max(0.0, min(0.25, float(margin)))
    suggested = dict(current.to_dict())
    metric_to_auto = {
        "overall_score": "auto_publish_min_overall",
        "traceability_score": "auto_publish_min_traceability",
        "actionability_score": "auto_publish_min_actionability",
        "coverage_score": "auto_publish_min_coverage",
        "consistency_score": "auto_publish_min_consistency",
        "noise_score": "auto_publish_min_noise",
        "novelty_score": "auto_publish_min_novelty",
    }
    metric_to_reject = {
        "overall_score": "reject_max_overall",
        "traceability_score": "reject_max_traceability",
        "actionability_score": "reject_max_actionability",
        "coverage_score": "reject_max_coverage",
        "consistency_score": "reject_max_consistency",
        "noise_score": "reject_max_noise",
    }

    for score_key, threshold_key in metric_to_auto.items():
        auto_values = _values_for_decision(samples, "auto_publish", score_key)
        if auto_values:
            suggested[threshold_key] = _round(min(auto_values) - safe_margin)

    for score_key, threshold_key in metric_to_reject.items():
        reject_values = _values_for_decision(samples, "reject", score_key)
        if reject_values:
            suggested[threshold_key] = _round(max(reject_values) + safe_margin)

    pair_keys = (
        ("reject_max_overall", "auto_publish_min_overall"),
        ("reject_max_traceability", "auto_publish_min_traceability"),
        ("reject_max_actionability", "auto_publish_min_actionability"),
        ("reject_max_coverage", "auto_publish_min_coverage"),
        ("reject_max_consistency", "auto_publish_min_consistency"),
        ("reject_max_noise", "auto_publish_min_noise"),
    )
    for reject_key, auto_key in pair_keys:
        reject_value = float(suggested[reject_key])
        auto_value = float(suggested[auto_key])
        if reject_value < auto_value:
            continue
        midpoint = (reject_value + auto_value) / 2.0
        suggested[reject_key] = _round(midpoint - 0.02)
        suggested[auto_key] = _round(midpoint + 0.02)

    return suggested


def build_report(manifest: dict[str, Any], *, margin: float = 0.03) -> dict[str, Any]:
    normalized_samples = [_normalize_sample(item) for item in manifest["samples"]]
    policy = ReviewPolicy()
    evaluations, mismatches = _compare_samples(normalized_samples, policy)
    confusion = _decision_confusion_matrix()
    reviewer_counts = {item: 0 for item in DECISIONS}
    policy_counts = {item: 0 for item in DECISIONS}

    for item in evaluations:
        reviewer = item["reviewer_decision"]
        predicted = item["policy_decision"]
        reviewer_counts[reviewer] += 1
        policy_counts[predicted] += 1
        confusion[reviewer][predicted] += 1

    matched_count = sum(1 for item in evaluations if item["matched"])
    total_count = len(evaluations)
    accuracy = _round(float(matched_count) / float(max(total_count, 1)))
    current_thresholds = policy.thresholds.to_dict()
    suggested_thresholds = _suggest_thresholds(samples=normalized_samples, current=policy.thresholds, margin=margin)
    delta_thresholds = {
        key: round(float(suggested_thresholds[key]) - float(current_thresholds[key]), 4)
        for key in current_thresholds.keys()
    }
    reviewer_confidences = [
        float(sample["reviewer_judgement"].get("confidence", 0.0))
        for sample in normalized_samples
    ]

    return {
        "manifest_id": str(manifest.get("manifest_id", "")).strip() or "unknown",
        "manifest_version": str(manifest.get("manifest_version", "")).strip() or "unknown",
        "sample_count": total_count,
        "agreement": {
            "matched": matched_count,
            "mismatched": total_count - matched_count,
            "accuracy": accuracy,
            "average_reviewer_confidence": _round(mean(reviewer_confidences)) if reviewer_confidences else 0.0,
        },
        "decision_breakdown": {
            "reviewer": reviewer_counts,
            "policy": policy_counts,
        },
        "confusion_matrix": confusion,
        "mismatches": mismatches,
        "thresholds": {
            "current": current_thresholds,
            "suggested": suggested_thresholds,
            "delta": delta_thresholds,
        },
        "sample_evaluations": evaluations,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest).resolve()
    output_path = Path(args.output).resolve() if str(args.output).strip() != "-" else None
    try:
        manifest = load_manifest(manifest_path)
        report = build_report(manifest, margin=float(args.margin))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Calibration failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_report(output_path, report)
        print("Calibration report written: %s" % output_path)

    print(
        "Calibration samples=%s matched=%s mismatched=%s accuracy=%.4f"
        % (
            report["sample_count"],
            report["agreement"]["matched"],
            report["agreement"]["mismatched"],
            report["agreement"]["accuracy"],
        )
    )
    if report["mismatches"]:
        print("Mismatched samples: %s" % ", ".join(item["sample_id"] for item in report["mismatches"]))
    else:
        print("Mismatched samples: none")

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.fail_on_mismatch and report["agreement"]["mismatched"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
