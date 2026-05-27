from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "controlled-trial-run-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-summary.md"
)
DEFAULT_MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-metrics-manifest.json"
)

SUPPORTED_EVIDENCE_ORIGINS = {"real", "fixture", "synthetic"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect and classify real controlled-trial loop evidence for GL-12 launch-gate progress tracking."
        )
    )
    parser.add_argument(
        "--run-report",
        action="append",
        default=[],
        help=(
            "Path to controlled-trial run report JSON. Repeat for multiple reports. "
            "Defaults to baselines/controlled-trial/controlled-trial-run-report.json."
        ),
    )
    parser.add_argument(
        "--loop-manifest",
        action="append",
        default=[],
        help=(
            "Path to real-trial loop manifest JSON with top-level loops list. Repeat for multiple inputs. "
            "Loop rows use the same schema as trial-metrics manifest loops."
        ),
    )
    parser.add_argument(
        "--loop-manifest-dir",
        action="append",
        default=[],
        help=(
            "Directory containing real-trial loop manifest JSON files. Repeat for multiple directories. "
            "Files are discovered using --loop-manifest-pattern."
        ),
    )
    parser.add_argument(
        "--loop-manifest-pattern",
        default="*.json",
        help=(
            "Glob pattern used when expanding --loop-manifest-dir (default: *.json). "
            "Use **/*.json with --loop-manifest-recursive for nested manifests."
        ),
    )
    parser.add_argument(
        "--loop-manifest-recursive",
        action="store_true",
        help="Recursively scan --loop-manifest-dir using the provided glob pattern.",
    )
    parser.add_argument(
        "--strict-loop-manifest-contract",
        action="store_true",
        help=(
            "Fail when any --loop-manifest or --loop-manifest-dir JSON file does not provide top-level loops list. "
            "Default behavior is to skip non-loop-manifest JSON files discovered during batch intake."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Collection report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Collection summary markdown output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--manifest-output",
        default=str(DEFAULT_MANIFEST_PATH),
        help='Optional trial-metrics manifest output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--minimum-complete-loops",
        type=int,
        default=10,
        help="Minimum launch-gate-eligible complete real loops.",
    )
    parser.add_argument(
        "--minimum-modalities",
        type=int,
        default=4,
        help="Minimum launch-gate-eligible modality coverage from real loops.",
    )
    parser.add_argument(
        "--release-decision",
        default="GO",
        choices=["GO", "HOLD"],
        help="Release decision value written into emitted trial-metrics manifest.",
    )
    parser.add_argument(
        "--operator-cost-accepted",
        default="true",
        choices=["true", "false"],
        help="Whether cost-per-accepted-skill is operator accepted in emitted manifest.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print full JSON collection report to stdout.",
    )
    parser.add_argument(
        "--fail-on-blocker",
        action="store_true",
        help="Exit with code 1 when collection report contains blockers.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return bool(default)
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return bool(default)


def _is_utc_timestamp(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _normalize_evidence_origin(raw: Any, *, loop_id: str) -> str:
    normalized = str(raw if raw is not None else "unspecified").strip().lower() or "unspecified"
    if normalized != "unspecified" and normalized not in SUPPORTED_EVIDENCE_ORIGINS:
        raise ValueError(
            "Loop %s has unsupported evidence_origin: %s (valid: %s)."
            % (loop_id, normalized, ", ".join(sorted(SUPPORTED_EVIDENCE_ORIGINS)))
        )
    return normalized


def _normalize_loop_row(loop_metrics: dict[str, Any], *, sample_id: str, source_report_path: Path) -> dict[str, Any]:
    loop_id = str(loop_metrics.get("loop_id", "")).strip() or sample_id
    if not loop_id:
        raise ValueError("Loop row missing loop_id and sample_id fallback in %s" % source_report_path)

    modality = str(loop_metrics.get("modality", "")).strip().lower()
    if not modality:
        raise ValueError("Loop %s missing modality in %s" % (loop_id, source_report_path))

    status = str(loop_metrics.get("status", "complete")).strip().lower()
    if status not in {"complete", "incomplete"}:
        raise ValueError("Loop %s status must be complete or incomplete." % loop_id)

    evidence_origin = _normalize_evidence_origin(loop_metrics.get("evidence_origin", "unspecified"), loop_id=loop_id)
    launch_gate_eligible = (
        _to_bool(loop_metrics.get("launch_gate_eligible"), default=False)
        if "launch_gate_eligible" in loop_metrics
        else evidence_origin == "real"
    )
    if launch_gate_eligible and evidence_origin != "real":
        raise ValueError("Loop %s cannot be launch_gate_eligible unless evidence_origin is real." % loop_id)

    launch_gate_ineligible_reason = str(loop_metrics.get("launch_gate_ineligible_reason", "")).strip()
    if not launch_gate_eligible and not launch_gate_ineligible_reason:
        if evidence_origin == "fixture":
            launch_gate_ineligible_reason = "fixture_evidence_not_launch_gate_eligible"
        elif evidence_origin == "synthetic":
            launch_gate_ineligible_reason = "synthetic_evidence_not_launch_gate_eligible"
        elif evidence_origin == "unspecified":
            launch_gate_ineligible_reason = "missing_evidence_origin_label"
        else:
            launch_gate_ineligible_reason = "explicitly_marked_not_launch_gate_eligible"

    row = {
        "loop_id": loop_id,
        "status": status,
        "modality": modality,
        "evidence_origin": evidence_origin,
        "launch_gate_eligible": launch_gate_eligible,
        "launch_gate_ineligible_reason": launch_gate_ineligible_reason,
        "review_outcome": str(loop_metrics.get("review_outcome", "unknown")).strip().lower() or "unknown",
        "revisions_before_approval": int(loop_metrics.get("revisions_before_approval", 0) or 0),
        "reviewer_edit_distance_pct": float(loop_metrics.get("reviewer_edit_distance_pct", 0.0) or 0.0),
        "agent_smoke_result": str(loop_metrics.get("agent_smoke_result", "not_run")).strip().lower() or "not_run",
        "published_without_review": bool(loop_metrics.get("published_without_review", False)),
        "critical_secret_or_pii_leak": bool(loop_metrics.get("critical_secret_or_pii_leak", False)),
        "high_severity_incident": bool(loop_metrics.get("high_severity_incident", False)),
        "latency_ms": float(loop_metrics.get("latency_ms", 0.0) or 0.0),
        "provider_failure_count": int(loop_metrics.get("provider_failure_count", 0) or 0),
        "provider_call_count": int(loop_metrics.get("provider_call_count", 0) or 0),
        "retry_count": int(loop_metrics.get("retry_count", 0) or 0),
        "artifact_count": int(loop_metrics.get("artifact_count", 0) or 0),
        "estimated_cost_usd": float(loop_metrics.get("estimated_cost_usd", 0.0) or 0.0),
        "review_task_id": str(loop_metrics.get("review_task_id", "")).strip(),
        "reviewed_by": str(loop_metrics.get("reviewed_by", "")).strip(),
        "reviewed_at_utc": str(loop_metrics.get("reviewed_at_utc", "")).strip(),
        "source_report_path": str(source_report_path),
    }

    if evidence_origin == "real":
        row["source_system"] = str(loop_metrics.get("source_system", "")).strip()
        row["source_reference"] = str(loop_metrics.get("source_reference", "")).strip()
        row["collected_at_utc"] = str(loop_metrics.get("collected_at_utc", "")).strip()
    return row


def _collect_loop_rows(
    *,
    run_reports: list[Path],
    loop_manifests: list[Path],
    strict_loop_manifest_contract: bool,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    deduped: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    skipped_non_loop_manifest_paths: list[str] = []

    for path in run_reports:
        payload = _read_json(path)
        samples = payload.get("samples")
        if not isinstance(samples, list):
            raise ValueError("Run report samples must be a list: %s" % path)
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            sample_id = str(sample.get("sample_id", "")).strip()
            loop_metrics = sample.get("loop_metrics")
            if not isinstance(loop_metrics, dict):
                continue
            row = _normalize_loop_row(loop_metrics, sample_id=sample_id, source_report_path=path)
            loop_id = str(row["loop_id"])
            if loop_id in deduped:
                duplicates.append(loop_id)
            deduped[loop_id] = row

    for path in loop_manifests:
        payload = _read_json(path)
        loops = payload.get("loops")
        if not isinstance(loops, list):
            if strict_loop_manifest_contract:
                raise ValueError("Loop manifest loops must be a list: %s" % path)
            skipped_non_loop_manifest_paths.append(str(path))
            continue
        for index, loop_metrics in enumerate(loops):
            if not isinstance(loop_metrics, dict):
                continue
            fallback_sample_id = "manifest-%s" % index
            row = _normalize_loop_row(loop_metrics, sample_id=fallback_sample_id, source_report_path=path)
            loop_id = str(row["loop_id"])
            if loop_id in deduped:
                duplicates.append(loop_id)
            deduped[loop_id] = row
    return list(deduped.values()), sorted(set(duplicates)), skipped_non_loop_manifest_paths


def _resolve_loop_manifest_paths(
    *,
    explicit_paths: list[str],
    manifest_dirs: list[str],
    pattern: str,
    recursive: bool,
) -> tuple[list[Path], list[Path]]:
    resolved_explicit_paths = [Path(item).resolve() for item in explicit_paths if str(item).strip()]
    resolved_manifest_dirs = [Path(item).resolve() for item in manifest_dirs if str(item).strip()]

    discovered_from_dirs: list[Path] = []
    normalized_pattern = str(pattern or "").strip() or "*.json"
    for directory in resolved_manifest_dirs:
        if not directory.is_dir():
            raise ValueError("Loop manifest directory does not exist or is not a directory: %s" % directory)
        iterator = directory.rglob(normalized_pattern) if recursive else directory.glob(normalized_pattern)
        discovered_from_dirs.extend(path.resolve() for path in iterator if path.is_file())

    deduped_paths: dict[str, Path] = {}
    for path in resolved_explicit_paths:
        deduped_paths[str(path)] = path
    for path in sorted(discovered_from_dirs, key=lambda value: str(value)):
        deduped_paths[str(path)] = path
    return list(deduped_paths.values()), resolved_manifest_dirs


def _build_collection_report(
    *,
    loops: list[dict[str, Any]],
    run_report_paths: list[Path],
    loop_manifest_paths: list[Path],
    loop_manifest_dirs: list[Path],
    duplicate_loop_ids: list[str],
    skipped_non_loop_manifest_paths: list[str],
    minimum_complete_loops: int,
    minimum_modalities: int,
) -> dict[str, Any]:
    evidence_origin_counts: dict[str, int] = {}
    launch_gate_ineligible_reason_counts: dict[str, int] = {}
    missing_trace_count = 0
    missing_review_trace_count = 0

    real_loops: list[dict[str, Any]] = []
    real_eligible_complete_loops: list[dict[str, Any]] = []
    launch_gate_modalities: set[str] = set()

    for loop in loops:
        evidence_origin = str(loop.get("evidence_origin", "unspecified"))
        evidence_origin_counts[evidence_origin] = evidence_origin_counts.get(evidence_origin, 0) + 1

        if not bool(loop.get("launch_gate_eligible", False)):
            reason = str(loop.get("launch_gate_ineligible_reason", "")).strip() or "unspecified_ineligible_reason"
            launch_gate_ineligible_reason_counts[reason] = launch_gate_ineligible_reason_counts.get(reason, 0) + 1

        if evidence_origin == "real":
            real_loops.append(loop)
            has_trace = bool(
                str(loop.get("source_system", "")).strip()
                and str(loop.get("source_reference", "")).strip()
                and str(loop.get("collected_at_utc", "")).strip()
            )
            if not has_trace:
                missing_trace_count += 1
            has_review_trace = bool(
                str(loop.get("review_task_id", "")).strip()
                and str(loop.get("reviewed_by", "")).strip()
                and _is_utc_timestamp(loop.get("reviewed_at_utc"))
            )
            if not has_review_trace:
                missing_review_trace_count += 1

        if (
            evidence_origin == "real"
            and bool(loop.get("launch_gate_eligible", False))
            and str(loop.get("status", "")).strip().lower() == "complete"
        ):
            real_eligible_complete_loops.append(loop)
            launch_gate_modalities.add(str(loop.get("modality", "")).strip().lower())

    launch_gate_eligible_complete_loop_count = len(real_eligible_complete_loops)
    launch_gate_eligible_modalities = sorted(item for item in launch_gate_modalities if item)
    launch_gate_eligible_modality_count = len(launch_gate_eligible_modalities)

    blockers: list[str] = []
    if missing_trace_count > 0:
        blockers.append("real_loop_source_trace_incomplete")
    if missing_review_trace_count > 0:
        blockers.append("real_loop_review_trace_incomplete")
    if launch_gate_eligible_complete_loop_count < minimum_complete_loops:
        blockers.append("real_loop_volume_below_threshold")
    if launch_gate_eligible_modality_count < minimum_modalities:
        blockers.append("real_loop_modality_coverage_below_threshold")

    program_status = "READY_FOR_CONTROLLED_BETA_EVIDENCE" if not blockers else "COLLECTION_INCOMPLETE"

    report = {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": _utc_now_iso(),
        "source_run_report_paths": [str(path) for path in run_report_paths],
        "source_loop_manifest_paths": [str(path) for path in loop_manifest_paths],
        "source_loop_manifest_dirs": [str(path) for path in loop_manifest_dirs],
        "input_report_count": len(run_report_paths),
        "input_loop_manifest_count": len(loop_manifest_paths),
        "ingested_loop_manifest_count": max(0, len(loop_manifest_paths) - len(skipped_non_loop_manifest_paths)),
        "input_loop_manifest_dir_count": len(loop_manifest_dirs),
        "skipped_non_loop_manifest_count": len(skipped_non_loop_manifest_paths),
        "skipped_non_loop_manifest_paths": skipped_non_loop_manifest_paths,
        "input_source_count": len(run_report_paths) + len(loop_manifest_paths),
        "deduplicated_loop_count": len(loops),
        "duplicate_loop_ids": duplicate_loop_ids,
        "evidence_origin_counts": evidence_origin_counts,
        "launch_gate_ineligible_reason_counts": launch_gate_ineligible_reason_counts,
        "launch_gate_alignment": {
            "program_status": program_status,
            "minimum_complete_loops": minimum_complete_loops,
            "minimum_modalities": minimum_modalities,
            "launch_gate_eligible_complete_loop_count": launch_gate_eligible_complete_loop_count,
            "launch_gate_eligible_modalities": launch_gate_eligible_modalities,
            "launch_gate_eligible_modality_count": launch_gate_eligible_modality_count,
            "missing_complete_loops_to_threshold": max(
                0, minimum_complete_loops - launch_gate_eligible_complete_loop_count
            ),
            "missing_modalities_to_threshold": max(0, minimum_modalities - launch_gate_eligible_modality_count),
            "real_evidence_loop_count": len(real_loops),
            "real_evidence_missing_source_trace_count": missing_trace_count,
            "real_evidence_missing_review_trace_count": missing_review_trace_count,
            "blockers": blockers,
        },
        "collected_real_launch_gate_eligible_loops": [
            {
                "loop_id": str(loop.get("loop_id", "")),
                "modality": str(loop.get("modality", "")),
                "source_system": str(loop.get("source_system", "")),
                "source_reference": str(loop.get("source_reference", "")),
                "collected_at_utc": str(loop.get("collected_at_utc", "")),
                "review_task_id": str(loop.get("review_task_id", "")),
                "reviewed_by": str(loop.get("reviewed_by", "")),
                "reviewed_at_utc": str(loop.get("reviewed_at_utc", "")),
                "source_report_path": str(loop.get("source_report_path", "")),
            }
            for loop in real_eligible_complete_loops
        ],
    }
    return report


def _build_trial_metrics_manifest(
    *,
    loops: list[dict[str, Any]],
    release_decision: str,
    operator_cost_accepted: bool,
) -> dict[str, Any]:
    manifest_loops = []
    for loop in loops:
        row = dict(loop)
        row.pop("source_report_path", None)
        manifest_loops.append(row)
    return {
        "manifest_id": "gl12-real-trial-loop-collection",
        "manifest_version": "1.0",
        "generated_at_utc": _utc_now_iso(),
        "release_gate": {
            "latest_release_decision": str(release_decision).strip().upper(),
            "evidence_ref": "docs/current/status/baselines/e13-release-switch-decision-report.json",
        },
        "operator_signoff": {
            "cost_per_accepted_skill_accepted": bool(operator_cost_accepted),
            "notes": "GL-12 collected real-loop manifest for launch-gate progress tracking.",
        },
        "loops": manifest_loops,
    }


def _render_summary(report: dict[str, Any]) -> str:
    alignment = report.get("launch_gate_alignment", {})
    blockers = alignment.get("blockers", [])
    lines = [
        "# Real Trial Loop Collection Summary",
        "",
        "- Program status: `%s`" % str(alignment.get("program_status", "unknown")),
        "- Deduplicated loops: `%s`" % str(report.get("deduplicated_loop_count", 0)),
        "- Evidence origin counts: `%s`" % str(report.get("evidence_origin_counts", {})),
        "- Real loops: `%s`" % str(alignment.get("real_evidence_loop_count", 0)),
        "- Launch-gate-eligible complete real loops: `%s/%s`"
        % (
            str(alignment.get("launch_gate_eligible_complete_loop_count", 0)),
            str(alignment.get("minimum_complete_loops", 10)),
        ),
        "- Launch-gate-eligible real modalities: `%s/%s`"
        % (
            str(alignment.get("launch_gate_eligible_modality_count", 0)),
            str(alignment.get("minimum_modalities", 4)),
        ),
        "- Launch-gate-eligible modality list: `%s`"
        % ", ".join(str(item) for item in alignment.get("launch_gate_eligible_modalities", []) if str(item).strip()),
        "- Real loops missing source trace: `%s`"
        % str(alignment.get("real_evidence_missing_source_trace_count", 0)),
        "- Real loops missing review trace: `%s`"
        % str(alignment.get("real_evidence_missing_review_trace_count", 0)),
        "- Ingested loop manifests: `%s/%s`"
        % (
            str(report.get("ingested_loop_manifest_count", 0)),
            str(report.get("input_loop_manifest_count", 0)),
        ),
        "- Skipped non-loop-manifest JSON files: `%s`" % str(report.get("skipped_non_loop_manifest_count", 0)),
        "",
        "## Blockers",
    ]
    if blockers:
        for blocker in blockers:
            lines.append("- `%s`" % str(blocker))
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    run_report_values = [str(item).strip() for item in args.run_report if str(item).strip()]
    loop_manifest_values = [str(item).strip() for item in args.loop_manifest if str(item).strip()]
    loop_manifest_dir_values = [str(item).strip() for item in args.loop_manifest_dir if str(item).strip()]
    run_report_paths = [Path(item).resolve() for item in run_report_values]
    try:
        loop_manifest_paths, loop_manifest_dirs = _resolve_loop_manifest_paths(
            explicit_paths=loop_manifest_values,
            manifest_dirs=loop_manifest_dir_values,
            pattern=str(args.loop_manifest_pattern),
            recursive=bool(args.loop_manifest_recursive),
        )
    except ValueError as exc:
        print("Real trial loop collection failed: %s" % exc, file=sys.stderr)
        return 2
    if not run_report_paths and not loop_manifest_paths:
        run_report_paths = [DEFAULT_RUN_REPORT_PATH]

    output_path = None if str(args.output).strip() == "-" else Path(args.output).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(args.summary_output).resolve()
    manifest_path = None if str(args.manifest_output).strip() == "-" else Path(args.manifest_output).resolve()

    try:
        missing_paths = [path for path in run_report_paths if not path.is_file()]
        missing_paths.extend(path for path in loop_manifest_paths if not path.is_file())
        if missing_paths:
            raise ValueError("Missing run report path(s): %s" % ", ".join(str(path) for path in missing_paths))

        loops, duplicate_loop_ids, skipped_non_loop_manifest_paths = _collect_loop_rows(
            run_reports=run_report_paths,
            loop_manifests=loop_manifest_paths,
            strict_loop_manifest_contract=bool(args.strict_loop_manifest_contract),
        )
        if not loops:
            raise ValueError("No loop_metrics rows found in run report inputs.")

        report = _build_collection_report(
            loops=loops,
            run_report_paths=run_report_paths,
            loop_manifest_paths=loop_manifest_paths,
            loop_manifest_dirs=loop_manifest_dirs,
            duplicate_loop_ids=duplicate_loop_ids,
            skipped_non_loop_manifest_paths=skipped_non_loop_manifest_paths,
            minimum_complete_loops=max(1, int(args.minimum_complete_loops)),
            minimum_modalities=max(1, int(args.minimum_modalities)),
        )
        summary = _render_summary(report)
        manifest = _build_trial_metrics_manifest(
            loops=loops,
            release_decision=str(args.release_decision).strip().upper(),
            operator_cost_accepted=str(args.operator_cost_accepted).strip().lower() == "true",
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial loop collection failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial loop collection report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial loop collection summary written: %s" % summary_path)
    if manifest_path is not None:
        _write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print("Real trial loop metrics manifest written: %s" % manifest_path)

    alignment = report.get("launch_gate_alignment", {})
    blockers = alignment.get("blockers", [])
    print(
        "Real trial loop collection status=%s loops=%s real_eligible_complete=%s modalities=%s blockers=%s"
        % (
            str(alignment.get("program_status", "unknown")),
            int(report.get("deduplicated_loop_count", 0) or 0),
            int(alignment.get("launch_gate_eligible_complete_loop_count", 0) or 0),
            int(alignment.get("launch_gate_eligible_modality_count", 0) or 0),
            "none" if not blockers else ",".join(str(item) for item in blockers),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_blocker and blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
