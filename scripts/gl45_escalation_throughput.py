from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACKNOWLEDGEMENT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-report.json"
)
DEFAULT_COLLECTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-45 acknowledgement-throughput diagnostics by comparing GL-44 "
            "acknowledgement closure outcomes with GL-12 launch-gate-eligible real loop coverage."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-acknowledgements-report",
        default=str(DEFAULT_ACKNOWLEDGEMENT_REPORT_PATH),
    )
    parser.add_argument(
        "--collection-report",
        default=str(DEFAULT_COLLECTION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-throughput-report",
        default="",
        help=(
            "Optional previous GL-45 throughput report. When omitted, script attempts to read "
            "existing --output before writing for delta comparison."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-45 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-45 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Owner tag written into GL-45 report.",
    )
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help="Exit with code 1 when throughput status is ESCALATION_ACK_THROUGHPUT_STALLED.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _normalize_loop_ids(rows: Any) -> list[str]:
    if not isinstance(rows, list):
        return []
    loop_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        loop_id = str(row.get("loop_id", "")).strip()
        if loop_id:
            loop_ids.append(loop_id)
    return sorted(set(loop_ids))


def _normalize_ack_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
    return normalized


def _compute_ack_snapshot(ack_report: dict[str, Any]) -> dict[str, Any]:
    counts = ack_report.get("followup_resolution_escalation_acknowledgement_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    rows = _normalize_ack_rows(
        ack_report.get("followup_resolution_escalation_acknowledgement_rows", [])
    )

    resolved_loop_ids: set[str] = set()
    resolved_modality_counts: dict[str, int] = {}
    resolved_item_ids: set[str] = set()
    pending_or_blocked_item_ids: set[str] = set()

    for row in rows:
        ack_status = str(row.get("acknowledgement_status", "")).strip().lower()
        item_id = str(row.get("acknowledgement_item_id", "")).strip()
        loop_id = str(row.get("linked_submission_loop_id_gl24", "")).strip()
        modality = str(row.get("required_modality", "")).strip().lower()

        if ack_status == "resolved_acknowledged":
            if item_id:
                resolved_item_ids.add(item_id)
            if loop_id:
                resolved_loop_ids.add(loop_id)
            if modality:
                resolved_modality_counts[modality] = resolved_modality_counts.get(modality, 0) + 1
        elif ack_status in {"pending_ack", "blocked"} and item_id:
            pending_or_blocked_item_ids.add(item_id)

    return {
        "acknowledgement_status": str(
            ack_report.get("followup_resolution_escalation_acknowledgement_status", "unknown")
        ).strip(),
        "warning_codes": ack_report.get("warning_codes", []),
        "total_item_count": _to_int(counts.get("total_item_count", 0), default=len(rows)),
        "open_item_count": _to_int(counts.get("open_item_count", 0), default=0),
        "resolved_acknowledged_item_count": _to_int(
            counts.get("resolved_acknowledged_item_count", 0),
            default=0,
        ),
        "pending_ack_item_count": _to_int(counts.get("pending_ack_item_count", 0), default=0),
        "blocked_item_count": _to_int(counts.get("blocked_item_count", 0), default=0),
        "resolved_acknowledged_item_ids": sorted(resolved_item_ids),
        "pending_or_blocked_item_ids": sorted(pending_or_blocked_item_ids),
        "resolved_submission_loop_ids": sorted(resolved_loop_ids),
        "resolved_submission_modality_counts": {
            key: resolved_modality_counts[key] for key in sorted(resolved_modality_counts)
        },
    }


def _compute_collection_snapshot(collection_report: dict[str, Any]) -> dict[str, Any]:
    alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(alignment, dict):
        alignment = {}
    loop_rows = collection_report.get("collected_real_launch_gate_eligible_loops", [])
    loop_ids = _normalize_loop_ids(loop_rows)
    loop_modalities: dict[str, int] = {}
    if isinstance(loop_rows, list):
        for row in loop_rows:
            if not isinstance(row, dict):
                continue
            modality = str(row.get("modality", "")).strip().lower()
            if modality:
                loop_modalities[modality] = loop_modalities.get(modality, 0) + 1

    return {
        "program_status": str(alignment.get("program_status", "unknown")).strip(),
        "launch_gate_eligible_complete_loop_count": _to_int(
            alignment.get("launch_gate_eligible_complete_loop_count", 0),
            default=len(loop_ids),
        ),
        "launch_gate_eligible_modality_count": _to_int(
            alignment.get("launch_gate_eligible_modality_count", 0),
            default=len(loop_modalities),
        ),
        "missing_complete_loops_to_threshold": _to_int(
            alignment.get("missing_complete_loops_to_threshold", 0),
            default=0,
        ),
        "missing_modalities_to_threshold": _to_int(
            alignment.get("missing_modalities_to_threshold", 0),
            default=0,
        ),
        "launch_gate_eligible_loop_ids": loop_ids,
        "launch_gate_eligible_modality_counts": {
            key: loop_modalities[key] for key in sorted(loop_modalities)
        },
    }


def _normalize_previous_snapshot(previous_report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ack_snapshot = previous_report.get("acknowledgement_snapshot", {})
    if not isinstance(ack_snapshot, dict):
        ack_snapshot = {}
    collection_snapshot = previous_report.get("collection_snapshot", {})
    if not isinstance(collection_snapshot, dict):
        collection_snapshot = {}

    return (
        {
            "resolved_acknowledged_item_count": _to_int(
                ack_snapshot.get("resolved_acknowledged_item_count", 0),
                default=0,
            ),
            "resolved_submission_loop_ids": sorted(
                set(str(item).strip() for item in ack_snapshot.get("resolved_submission_loop_ids", []) if str(item).strip())
            ),
            "resolved_acknowledged_item_ids": sorted(
                set(str(item).strip() for item in ack_snapshot.get("resolved_acknowledged_item_ids", []) if str(item).strip())
            ),
        },
        {
            "launch_gate_eligible_complete_loop_count": _to_int(
                collection_snapshot.get("launch_gate_eligible_complete_loop_count", 0),
                default=0,
            ),
            "launch_gate_eligible_loop_ids": sorted(
                set(str(item).strip() for item in collection_snapshot.get("launch_gate_eligible_loop_ids", []) if str(item).strip())
            ),
        },
    )


def _build_status(
    *,
    previous_available: bool,
    missing_complete_loops_to_threshold: int,
    missing_modalities_to_threshold: int,
    ack_open_item_count: int,
    net_new_resolved_ack_item_count: int,
    net_new_resolved_submission_loop_count: int,
    net_new_launch_gate_eligible_loop_count: int,
    unresolved_ack_closed_loop_count: int,
) -> str:
    if ack_open_item_count <= 0 and missing_complete_loops_to_threshold <= 0 and missing_modalities_to_threshold <= 0:
        return "ESCALATION_ACK_THROUGHPUT_THRESHOLD_MET"
    if not previous_available:
        return "ESCALATION_ACK_THROUGHPUT_BASELINE_INITIALIZED"
    if (
        net_new_resolved_ack_item_count > 0
        or net_new_resolved_submission_loop_count > 0
        or net_new_launch_gate_eligible_loop_count > 0
    ):
        if unresolved_ack_closed_loop_count > 0:
            return "ESCALATION_ACK_THROUGHPUT_PARTIAL_PROGRESS"
        return "ESCALATION_ACK_THROUGHPUT_PROGRESSING"
    return "ESCALATION_ACK_THROUGHPUT_STALLED"


def _build_report(
    *,
    acknowledgement_report: dict[str, Any],
    acknowledgement_report_path: Path,
    collection_report: dict[str, Any],
    collection_report_path: Path,
    previous_report: dict[str, Any] | None,
    previous_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    ack_snapshot = _compute_ack_snapshot(acknowledgement_report)
    collection_snapshot = _compute_collection_snapshot(collection_report)

    previous_available = isinstance(previous_report, dict)
    if previous_available and previous_report is not None:
        previous_ack_snapshot, previous_collection_snapshot = _normalize_previous_snapshot(previous_report)
    else:
        previous_ack_snapshot, previous_collection_snapshot = (
            {
                "resolved_acknowledged_item_count": 0,
                "resolved_submission_loop_ids": [],
                "resolved_acknowledged_item_ids": [],
            },
            {
                "launch_gate_eligible_complete_loop_count": 0,
                "launch_gate_eligible_loop_ids": [],
            },
        )

    current_resolved_ack_item_ids = set(ack_snapshot["resolved_acknowledged_item_ids"])
    previous_resolved_ack_item_ids = set(previous_ack_snapshot["resolved_acknowledged_item_ids"])
    current_resolved_submission_loop_ids = set(ack_snapshot["resolved_submission_loop_ids"])
    previous_resolved_submission_loop_ids = set(previous_ack_snapshot["resolved_submission_loop_ids"])
    current_launch_gate_loop_ids = set(collection_snapshot["launch_gate_eligible_loop_ids"])
    previous_launch_gate_loop_ids = set(previous_collection_snapshot["launch_gate_eligible_loop_ids"])

    net_new_resolved_ack_item_ids = sorted(current_resolved_ack_item_ids - previous_resolved_ack_item_ids)
    net_new_resolved_submission_loop_ids = sorted(
        current_resolved_submission_loop_ids - previous_resolved_submission_loop_ids
    )
    net_new_launch_gate_eligible_loop_ids = sorted(current_launch_gate_loop_ids - previous_launch_gate_loop_ids)

    unresolved_ack_closed_loop_ids = sorted(
        loop_id
        for loop_id in current_resolved_submission_loop_ids
        if loop_id and loop_id not in current_launch_gate_loop_ids
    )

    delta = {
        "resolved_acknowledged_item_count": _to_int(
            ack_snapshot["resolved_acknowledged_item_count"], default=0
        )
        - _to_int(previous_ack_snapshot["resolved_acknowledged_item_count"], default=0),
        "launch_gate_eligible_complete_loop_count": _to_int(
            collection_snapshot["launch_gate_eligible_complete_loop_count"], default=0
        )
        - _to_int(previous_collection_snapshot["launch_gate_eligible_complete_loop_count"], default=0),
        "net_new_resolved_acknowledged_item_count": len(net_new_resolved_ack_item_ids),
        "net_new_resolved_submission_loop_count": len(net_new_resolved_submission_loop_ids),
        "net_new_launch_gate_eligible_loop_count": len(net_new_launch_gate_eligible_loop_ids),
        "unresolved_ack_closed_loop_count": len(unresolved_ack_closed_loop_ids),
    }

    throughput_status = _build_status(
        previous_available=previous_available,
        missing_complete_loops_to_threshold=_to_int(
            collection_snapshot["missing_complete_loops_to_threshold"], default=0
        ),
        missing_modalities_to_threshold=_to_int(
            collection_snapshot["missing_modalities_to_threshold"], default=0
        ),
        ack_open_item_count=_to_int(ack_snapshot["open_item_count"], default=0),
        net_new_resolved_ack_item_count=delta["net_new_resolved_acknowledged_item_count"],
        net_new_resolved_submission_loop_count=delta["net_new_resolved_submission_loop_count"],
        net_new_launch_gate_eligible_loop_count=delta["net_new_launch_gate_eligible_loop_count"],
        unresolved_ack_closed_loop_count=delta["unresolved_ack_closed_loop_count"],
    )

    warning_codes: list[str] = []
    if delta["net_new_resolved_acknowledged_item_count"] <= 0 and previous_available:
        warning_codes.append("no_net_new_resolved_acknowledgements")
    if delta["net_new_launch_gate_eligible_loop_count"] <= 0 and previous_available:
        warning_codes.append("no_net_new_launch_gate_eligible_real_loops")
    if delta["unresolved_ack_closed_loop_count"] > 0:
        warning_codes.append("resolved_acknowledgements_not_visible_in_launch_gate_eligible_loops")
    if _to_int(collection_snapshot["missing_modalities_to_threshold"], default=0) > 0:
        warning_codes.append("modality_gap_persists")
    if _to_int(collection_snapshot["missing_complete_loops_to_threshold"], default=0) > 0:
        warning_codes.append("loop_volume_gap_persists")
    if _to_int(ack_snapshot["open_item_count"], default=0) > 0:
        warning_codes.append("open_acknowledgement_items_present")
    warning_codes.extend(
        str(item).strip()
        for item in ack_snapshot.get("warning_codes", [])
        if str(item).strip()
    )
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_throughput.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_acknowledgements_report": str(
                acknowledgement_report_path
            ),
            "collection_report": str(collection_report_path),
            "previous_throughput_report": str(previous_report_path) if previous_report_path else "",
        },
        "followup_resolution_escalation_acknowledgement_status_gl44": str(
            ack_snapshot.get("acknowledgement_status", "unknown")
        ),
        "collection_program_status_gl12": str(collection_snapshot.get("program_status", "unknown")),
        "followup_resolution_escalation_throughput_status": throughput_status,
        "warning_codes": warning_codes,
        "acknowledgement_snapshot": ack_snapshot,
        "collection_snapshot": collection_snapshot,
        "snapshot_delta": delta,
        "net_new_resolved_acknowledged_item_ids": net_new_resolved_ack_item_ids,
        "net_new_resolved_submission_loop_ids": net_new_resolved_submission_loop_ids,
        "net_new_launch_gate_eligible_loop_ids": net_new_launch_gate_eligible_loop_ids,
        "unresolved_acknowledged_submission_loop_ids": unresolved_ack_closed_loop_ids,
    }


def _render_summary(report: dict[str, Any]) -> str:
    ack_snapshot = report.get("acknowledgement_snapshot", {})
    if not isinstance(ack_snapshot, dict):
        ack_snapshot = {}
    collection_snapshot = report.get("collection_snapshot", {})
    if not isinstance(collection_snapshot, dict):
        collection_snapshot = {}
    delta = report.get("snapshot_delta", {})
    if not isinstance(delta, dict):
        delta = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Throughput Summary",
        "",
        "- GL-45 throughput status: `%s`"
        % str(report.get("followup_resolution_escalation_throughput_status", "unknown")),
        "- GL-44 acknowledgement status: `%s`"
        % str(report.get("followup_resolution_escalation_acknowledgement_status_gl44", "unknown")),
        "- GL-12 collection status: `%s`" % str(report.get("collection_program_status_gl12", "unknown")),
        "- Resolved acknowledgements: `%s`"
        % str(_to_int(ack_snapshot.get("resolved_acknowledged_item_count", 0), default=0)),
        "- Open acknowledgement items: `%s`"
        % str(_to_int(ack_snapshot.get("open_item_count", 0), default=0)),
        "- Launch-gate-eligible real loops: `%s`"
        % str(_to_int(collection_snapshot.get("launch_gate_eligible_complete_loop_count", 0), default=0)),
        "- Missing loops to threshold: `%s`"
        % str(_to_int(collection_snapshot.get("missing_complete_loops_to_threshold", 0), default=0)),
        "- Missing modalities to threshold: `%s`"
        % str(_to_int(collection_snapshot.get("missing_modalities_to_threshold", 0), default=0)),
        "- Net new resolved acknowledgements: `%s`"
        % str(_to_int(delta.get("net_new_resolved_acknowledged_item_count", 0), default=0)),
        "- Net new resolved submission loops: `%s`"
        % str(_to_int(delta.get("net_new_resolved_submission_loop_count", 0), default=0)),
        "- Net new launch-gate-eligible loops: `%s`"
        % str(_to_int(delta.get("net_new_launch_gate_eligible_loop_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    unresolved_loop_ids = report.get("unresolved_acknowledged_submission_loop_ids", [])
    if not isinstance(unresolved_loop_ids, list):
        unresolved_loop_ids = []
    lines.extend(["", "## Acknowledged-But-Unmapped Loops"])
    if unresolved_loop_ids:
        for loop_id in unresolved_loop_ids:
            lines.append("- `%s`" % str(loop_id))
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    acknowledgement_report_path = Path(
        str(args.submission_queue_followup_resolution_escalation_acknowledgements_report).strip()
    ).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = (
        None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    )
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not acknowledgement_report_path.is_file():
            raise ValueError(
                "GL-44 acknowledgement report path does not exist: %s" % acknowledgement_report_path
            )
        if not collection_report_path.is_file():
            raise ValueError("GL-12 collection report path does not exist: %s" % collection_report_path)
        acknowledgement_report = _read_json(acknowledgement_report_path)
        collection_report = _read_json(collection_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_throughput_report).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            acknowledgement_report=acknowledgement_report,
            acknowledgement_report_path=acknowledgement_report_path,
            collection_report=collection_report,
            collection_report_path=collection_report_path,
            previous_report=previous_report,
            previous_report_path=previous_report_path if previous_report is not None else None,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation throughput generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation throughput report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation throughput summary written: %s"
            % summary_path
        )

    delta = report.get("snapshot_delta", {})
    if not isinstance(delta, dict):
        delta = {}
    print(
        "Real trial submission queue follow-up resolution escalation throughput status=%s net_new_ack=%s net_new_real_loops=%s"
        % (
            str(report.get("followup_resolution_escalation_throughput_status", "unknown")),
            _to_int(delta.get("net_new_resolved_acknowledged_item_count", 0), default=0),
            _to_int(delta.get("net_new_launch_gate_eligible_loop_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_stalled) and str(
        report.get("followup_resolution_escalation_throughput_status", "")
    ).strip().upper() == "ESCALATION_ACK_THROUGHPUT_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
