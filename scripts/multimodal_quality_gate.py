from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_TRIAL_BASELINE_DIR = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "real-trial-loop-collection"
DEFAULT_EVIDENCE_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-multimodal-quality-evidence.json"
DEFAULT_OUTPUT_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-multimodal-quality-gate-report.json"
DEFAULT_SUMMARY_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-multimodal-quality-gate-summary.md"

STATUS_EMPTY = "MULTIMODAL_QUALITY_GATE_EMPTY"
STATUS_READY = "MULTIMODAL_QUALITY_GATE_READY"
STATUS_BLOCKED = "MULTIMODAL_QUALITY_GATE_BLOCKED"

SCORE_FIELDS = [
    "faithfulness",
    "completeness",
    "reusability",
    "traceability",
    "safety_redaction",
    "agent_usability",
]
BETA_THRESHOLDS = {
    "faithfulness": 4.0,
    "traceability": 4.0,
    "safety_redaction": 5.0,
    "agent_usability": 4.0,
}
ALLOWED_MODALITIES = {"text", "audio", "image", "video", "tabular", "corpus", "mixed"}
APPROVED_REVIEW_DECISIONS = {"approved", "approved_for_beta_evidence", "pass", "passed"}
UNAVAILABLE_PROVIDER_STATUSES = {
    "unavailable",
    "provider_unavailable",
    "missing",
    "not_configured",
    "not_available",
    "failed",
}
PLACEHOLDER_TOKENS = {
    "",
    "example",
    "fixture",
    "fixme",
    "mock",
    "n/a",
    "na",
    "none",
    "null",
    "placeholder",
    "sample",
    "synthetic",
    "tbd",
    "todo",
    "unknown",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_modality(value: Any) -> str:
    return _normalize_text(value).lower()


def _normalize_status(value: Any) -> str:
    return _normalize_text(value).lower()


def _is_placeholder_text(value: Any) -> bool:
    text = _normalize_text(value)
    lowered = text.lower()
    if lowered in PLACEHOLDER_TOKENS:
        return True
    if "{{" in text or "}}" in text:
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    return False


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value is True
    return _normalize_text(value).lower() in {"true", "1", "yes"}


def _add_unique(target: list[str], code: str) -> None:
    if code not in target:
        target.append(code)


def _parse_required_modalities(value: str) -> list[str]:
    modalities: list[str] = []
    for item in str(value or "").split(","):
        modality = _normalize_modality(item)
        if modality:
            _add_unique(modalities, modality)
    return modalities


def _round(value: float) -> float:
    return round(float(value), 4)


def _to_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 1.0 or score > 5.0:
        return None
    return score


def _to_optional_rate(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        rate = float(value)
    except (TypeError, ValueError):
        return None
    if rate < 0.0 or rate > 1.0:
        return None
    return rate


def _provider_status_text(record: dict[str, Any], key: str) -> str:
    direct = _normalize_status(record.get(key))
    if direct:
        return direct
    provider_status = _as_dict(record.get("provider_status"))
    value = provider_status.get(key)
    if isinstance(value, dict):
        return _normalize_status(value.get("status"))
    return _normalize_status(value)


def _provider_metric(record: dict[str, Any], key: str) -> Any:
    if key in record:
        return record.get(key)
    provider_status = _as_dict(record.get("provider_status"))
    value = provider_status.get(key)
    if isinstance(value, dict):
        for metric_key in ("value", "confidence", "score"):
            if metric_key in value:
                return value.get(metric_key)
    return value


def _has_graceful_degradation_note(record: dict[str, Any]) -> bool:
    for key in ("graceful_degradation_note", "fallback_note", "provider_failure_note"):
        if _normalize_text(record.get(key)):
            return True
    return False


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        raw_records = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("quality_evidence"), list):
            raw_records = payload.get("quality_evidence")
        elif isinstance(payload.get("records"), list):
            raw_records = payload.get("records")
        elif isinstance(payload.get("samples"), list):
            raw_records = payload.get("samples")
        elif payload.get("loop_id") is not None:
            raw_records = [payload]
        else:
            raw_records = []
    else:
        raw_records = []

    records: list[dict[str, Any]] = []
    for item in raw_records:
        if isinstance(item, dict):
            records.append(item)
    return records


def load_quality_evidence(path: Path) -> tuple[list[dict[str, Any]], bool]:
    if not path.is_file():
        return [], True
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _extract_records(payload), False


def _validate_quality_record(
    record: dict[str, Any],
    *,
    min_ocr_confidence: float,
) -> dict[str, Any]:
    failure_codes: list[str] = []
    loop_id = _normalize_text(record.get("loop_id"))
    modality = _normalize_modality(record.get("modality"))

    if _is_placeholder_text(loop_id):
        _add_unique(failure_codes, "loop_id_missing_or_placeholder")
    if modality not in ALLOWED_MODALITIES:
        _add_unique(failure_codes, "modality_invalid")

    raw_scores = _as_dict(record.get("quality_scores"))
    normalized_scores: dict[str, float] = {}
    for field in SCORE_FIELDS:
        score = _to_score(raw_scores.get(field))
        if score is None:
            _add_unique(failure_codes, "quality_score_missing_or_invalid:%s" % field)
            continue
        normalized_scores[field] = score

    for field, threshold in BETA_THRESHOLDS.items():
        score = normalized_scores.get(field)
        if score is None:
            continue
        if score < threshold:
            _add_unique(failure_codes, "quality_score_below_beta_threshold:%s" % field)

    critical_issues = _as_list(record.get("critical_issues"))
    if critical_issues:
        _add_unique(failure_codes, "critical_issues_present")

    if not _is_true(record.get("requires_human_review")):
        _add_unique(failure_codes, "requires_human_review_not_true")
    if _normalize_status(record.get("human_review_decision")) not in APPROVED_REVIEW_DECISIONS:
        _add_unique(failure_codes, "human_review_decision_not_approved")

    if modality in {"image", "video"}:
        ocr_status = _provider_status_text(record, "ocr_status")
        if ocr_status in UNAVAILABLE_PROVIDER_STATUSES and not _has_graceful_degradation_note(record):
            _add_unique(failure_codes, "ocr_unavailable_without_graceful_degradation")

        raw_ocr_confidence = _provider_metric(record, "ocr_confidence")
        if raw_ocr_confidence not in (None, ""):
            ocr_confidence = _to_optional_rate(raw_ocr_confidence)
            if ocr_confidence is None:
                _add_unique(failure_codes, "ocr_confidence_invalid")
            elif ocr_confidence < min_ocr_confidence and not _as_list(record.get("uncertain_regions")):
                _add_unique(failure_codes, "ocr_low_confidence_without_uncertain_regions")

    if modality == "audio":
        asr_status = _provider_status_text(record, "asr_status")
        if asr_status in UNAVAILABLE_PROVIDER_STATUSES and _is_placeholder_text(record.get("transcript_ref")):
            _add_unique(failure_codes, "audio_asr_unavailable_without_transcript")

    if modality == "video":
        keyframe_status = _provider_status_text(record, "keyframe_status")
        if keyframe_status in UNAVAILABLE_PROVIDER_STATUSES and not _has_graceful_degradation_note(record):
            _add_unique(failure_codes, "video_keyframes_unavailable_without_graceful_degradation")

    status = "passed" if not failure_codes else "blocked"
    return {
        "loop_id": loop_id,
        "modality": modality,
        "status": status,
        "quality_scores": normalized_scores,
        "critical_issue_count": len(critical_issues),
        "minor_issue_count": len(_as_list(record.get("minor_issues"))),
        "requires_human_review": _is_true(record.get("requires_human_review")),
        "human_review_decision": _normalize_status(record.get("human_review_decision")),
        "failure_codes": failure_codes,
    }


def build_report(
    *,
    records: list[dict[str, Any]],
    evidence_path: Path,
    evidence_file_missing: bool,
    required_modalities: list[str],
    min_ocr_confidence: float = 0.7,
) -> dict[str, Any]:
    record_results = [
        _validate_quality_record(record, min_ocr_confidence=min_ocr_confidence)
        for record in records
    ]
    passed_records = [record for record in record_results if record.get("status") == "passed"]
    blocked_records = [record for record in record_results if record.get("status") != "passed"]
    covered_required_modalities = [
        modality
        for modality in required_modalities
        if any(record.get("modality") == modality for record in passed_records)
    ]
    missing_required_modalities = [
        modality for modality in required_modalities if modality not in set(covered_required_modalities)
    ]

    blocking_codes: list[str] = []
    for record in blocked_records:
        for code in _as_list(record.get("failure_codes")):
            _add_unique(blocking_codes, str(code))
    for modality in missing_required_modalities:
        _add_unique(blocking_codes, "required_modality_missing:%s" % modality)

    if not record_results:
        status = STATUS_EMPTY
    elif blocking_codes:
        status = STATUS_BLOCKED
    else:
        status = STATUS_READY

    score_averages: dict[str, float] = {}
    for field in SCORE_FIELDS:
        values = [
            float(_as_dict(record.get("quality_scores")).get(field))
            for record in record_results
            if field in _as_dict(record.get("quality_scores"))
        ]
        score_averages[field] = _round(mean(values)) if values else 0.0

    return {
        "schema_version": "multimodal_quality_gate.v1",
        "generated_at_utc": _utc_now_iso(),
        "status": status,
        "input_paths": {
            "quality_evidence": str(evidence_path),
            "quality_evidence_missing": evidence_file_missing,
        },
        "thresholds": {
            "beta_min_scores": BETA_THRESHOLDS,
            "no_critical_issues": True,
            "requires_human_review": True,
            "approved_human_review_decisions": sorted(APPROVED_REVIEW_DECISIONS),
            "min_ocr_confidence_before_uncertain_regions_required": min_ocr_confidence,
        },
        "required_modalities": required_modalities,
        "covered_required_modalities": covered_required_modalities,
        "missing_required_modalities": missing_required_modalities,
        "counts": {
            "quality_record_count": len(record_results),
            "passed_record_count": len(passed_records),
            "blocked_record_count": len(blocked_records),
            "required_modality_count": len(required_modalities),
            "covered_required_modality_count": len(covered_required_modalities),
            "missing_required_modality_count": len(missing_required_modalities),
        },
        "score_averages": score_averages,
        "blocking_codes": blocking_codes,
        "records": record_results,
    }


def render_summary(report: dict[str, Any]) -> str:
    counts = _as_dict(report.get("counts", {}))
    lines = [
        "# Multimodal Quality Gate Summary",
        "",
        "- Status: `%s`" % str(report.get("status", "unknown")),
        "- Quality records: `%s`" % str(counts.get("quality_record_count", 0)),
        "- Passed records: `%s`" % str(counts.get("passed_record_count", 0)),
        "- Blocked records: `%s`" % str(counts.get("blocked_record_count", 0)),
        "- Covered required modalities: `%s`"
        % (", ".join(str(item) for item in _as_list(report.get("covered_required_modalities"))) or "none"),
        "- Missing required modalities: `%s`"
        % (", ".join(str(item) for item in _as_list(report.get("missing_required_modalities"))) or "none"),
        "",
        "## Blocking Codes",
    ]
    blocking_codes = _as_list(report.get("blocking_codes"))
    if blocking_codes:
        lines.extend("- `%s`" % str(code) for code in blocking_codes)
    else:
        lines.append("- none")

    lines.extend(["", "## Records"])
    records = _as_list(report.get("records"))
    if records:
        for record in records:
            if not isinstance(record, dict):
                continue
            lines.append(
                "- `%s` modality=%s status=%s failures=%s"
                % (
                    str(record.get("loop_id", "")),
                    str(record.get("modality", "")),
                    str(record.get("status", "")),
                    ", ".join(str(code) for code in _as_list(record.get("failure_codes"))) or "none",
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate multimodal real-loop quality evidence before it can support launch evidence. "
            "This checks the P1 quality dimensions, human review decision, provider fallback notes, "
            "and required text/audio/image/video coverage."
        )
    )
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH), help="Quality evidence JSON path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help='Report output path. Use "-" to skip.')
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Markdown summary output path. Use "-" to skip.',
    )
    parser.add_argument(
        "--required-modalities",
        default="text,audio,image,video",
        help="Comma-separated modalities that must have passing quality evidence.",
    )
    parser.add_argument(
        "--min-ocr-confidence",
        type=float,
        default=0.7,
        help="Below this confidence, image/video records must include uncertain_regions.",
    )
    parser.add_argument("--fail-on-blocked", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    evidence_path = Path(str(args.evidence).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    required_modalities = _parse_required_modalities(str(args.required_modalities))

    try:
        records, evidence_file_missing = load_quality_evidence(evidence_path)
        report = build_report(
            records=records,
            evidence_path=evidence_path,
            evidence_file_missing=evidence_file_missing,
            required_modalities=required_modalities,
            min_ocr_confidence=float(args.min_ocr_confidence),
        )
        summary = render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Multimodal quality gate failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Multimodal quality gate report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Multimodal quality gate summary written: %s" % summary_path)

    counts = _as_dict(report.get("counts", {}))
    print(
        "Multimodal quality gate status=%s passed=%s blocked=%s missing_modalities=%s"
        % (
            str(report.get("status", "unknown")),
            str(counts.get("passed_record_count", 0)),
            str(counts.get("blocked_record_count", 0)),
            str(counts.get("missing_required_modality_count", 0)),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_blocked) and str(report.get("status", "")) != STATUS_READY:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
