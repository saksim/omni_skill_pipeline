from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_LOOP_COLLECTION_SCRIPT = REPO_ROOT / "scripts" / "run_real_trial_loop_collection.py"
REAL_LOOP_BACKFILL_EXECUTION_SCRIPT = REPO_ROOT / "scripts" / "run_real_trial_backfill_execution.py"
REAL_LOOP_BACKFILL_INTAKE_ACTIONS_SCRIPT = REPO_ROOT / "scripts" / "run_real_trial_backfill_intake_actions.py"
REAL_LOOP_BACKFILL_SUBMISSION_TEMPLATES_SCRIPT = (
    REPO_ROOT / "scripts" / "run_real_trial_backfill_submission_templates.py"
)
REAL_LOOP_BACKFILL_HANDOFF_SCRIPT = REPO_ROOT / "scripts" / "run_real_trial_backfill_handoff.py"
REAL_LOOP_BACKFILL_HANDOFF_ESCALATIONS_SCRIPT = (
    REPO_ROOT / "scripts" / "run_real_trial_backfill_handoff_escalations.py"
)
TRIAL_METRICS_COLLECTOR_SCRIPT = REPO_ROOT / "scripts" / "run_trial_metrics_collector.py"
LAUNCH_READINESS_GATE_SCRIPT = REPO_ROOT / "scripts" / "run_launch_readiness_gate.py"

DEFAULT_RUN_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "controlled-trial-run-report.json"
)
DEFAULT_COLLECTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_COLLECTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-summary.md"
)
DEFAULT_REAL_TRIAL_MANIFEST = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-metrics-manifest.json"
)
DEFAULT_BACKFILL_PLAN_OUTPUT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-backfill-plan.json"
)
DEFAULT_BACKFILL_EXECUTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-report.json"
)
DEFAULT_BACKFILL_EXECUTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-summary.md"
)
DEFAULT_BACKFILL_INTAKE_ACTIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-report.json"
)
DEFAULT_BACKFILL_INTAKE_ACTIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_MANIFEST_TEMPLATE = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-manifest.template.json"
)
DEFAULT_BACKFILL_HANDOFF_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_BACKFILL_HANDOFF_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-summary.md"
)
DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-report.json"
)
DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-summary.md"
)
DEFAULT_TRIAL_METRICS_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "trial-metrics-report.json"
)
DEFAULT_TRIAL_METRICS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "trial-metrics-summary.md"
)
DEFAULT_LAUNCH_READINESS_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "broad-launch-readiness-report.json"
)
DEFAULT_LAUNCH_READINESS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "broad-launch-readiness-summary.md"
)
DEFAULT_RELEASE_SWITCH_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "e13-release-switch-decision-report.json"
)
DEFAULT_CURRENT_STATUS_DOC = REPO_ROOT / "docs" / "current" / "status" / "CURRENT_STATUS.md"
DEFAULT_AGENT_SMOKE_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "agent-smoke-report.json"
)
DEFAULT_DOC_SYNC_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "e13-doc-sync-check-report.json"
)
DEFAULT_OPERATIONS_READINESS_REPORT = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "operations-readiness-report.json"
)
DEFAULT_EVIDENCE_PACK = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-launch-evidence-pack.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the real-trial launch evidence pipeline: "
            "GL-12 loop collection -> trial metrics report -> broad launch readiness gate."
        )
    )
    parser.add_argument(
        "--run-report",
        action="append",
        default=[],
        help="Path to controlled-trial run report JSON. Repeat for multiple inputs.",
    )
    parser.add_argument(
        "--loop-manifest",
        action="append",
        default=[],
        help=(
            "Path to loop manifest JSON with top-level loops list. Repeat for multiple inputs. "
            "Use this for real controlled external Beta loop evidence."
        ),
    )
    parser.add_argument(
        "--loop-manifest-dir",
        action="append",
        default=[],
        help=(
            "Directory containing loop manifest JSON files. Repeat for multiple directories. "
            "Use with --loop-manifest-pattern for batch ingestion."
        ),
    )
    parser.add_argument(
        "--loop-manifest-pattern",
        default="*.json",
        help="Glob pattern used when expanding --loop-manifest-dir (default: *.json).",
    )
    parser.add_argument(
        "--loop-manifest-recursive",
        action="store_true",
        help="Recursively scan --loop-manifest-dir when collecting loop manifests.",
    )
    parser.add_argument(
        "--strict-loop-manifest-contract",
        action="store_true",
        help=(
            "Fail when any loop-manifest JSON discovered by explicit path or directory input "
            "does not provide top-level loops list."
        ),
    )
    parser.add_argument("--collection-report-output", default=str(DEFAULT_COLLECTION_REPORT))
    parser.add_argument("--collection-summary-output", default=str(DEFAULT_COLLECTION_SUMMARY))
    parser.add_argument("--real-trial-manifest-output", default=str(DEFAULT_REAL_TRIAL_MANIFEST))
    parser.add_argument("--backfill-plan-output", default=str(DEFAULT_BACKFILL_PLAN_OUTPUT))
    parser.add_argument("--backfill-execution-output", default=str(DEFAULT_BACKFILL_EXECUTION_REPORT))
    parser.add_argument("--backfill-execution-summary-output", default=str(DEFAULT_BACKFILL_EXECUTION_SUMMARY))
    parser.add_argument("--backfill-intake-actions-output", default=str(DEFAULT_BACKFILL_INTAKE_ACTIONS_REPORT))
    parser.add_argument("--backfill-intake-actions-summary-output", default=str(DEFAULT_BACKFILL_INTAKE_ACTIONS_SUMMARY))
    parser.add_argument("--backfill-intake-owner", default="controlled-beta-ops")
    parser.add_argument("--backfill-submission-templates-output", default=str(DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_REPORT))
    parser.add_argument(
        "--backfill-submission-templates-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-manifest-template-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_MANIFEST_TEMPLATE),
    )
    parser.add_argument("--backfill-submission-owner", default="controlled-beta-ops")
    parser.add_argument("--backfill-handoff-output", default=str(DEFAULT_BACKFILL_HANDOFF_REPORT))
    parser.add_argument("--backfill-handoff-summary-output", default=str(DEFAULT_BACKFILL_HANDOFF_SUMMARY))
    parser.add_argument("--backfill-handoff-owner", default="controlled-beta-ops")
    parser.add_argument(
        "--backfill-handoff-escalations-output",
        default=str(DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_REPORT),
    )
    parser.add_argument(
        "--backfill-handoff-escalations-summary-output",
        default=str(DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_SUMMARY),
    )
    parser.add_argument("--backfill-handoff-escalations-owner", default="controlled-beta-ops")
    parser.add_argument(
        "--backfill-handoff-pending-ack-sla-hours",
        type=float,
        default=24.0,
        help="SLA threshold (hours) for GL-26 pending-ack aging diagnostics.",
    )
    parser.add_argument(
        "--backfill-handoff-pending-ack-overdue-hours",
        type=float,
        default=72.0,
        help="Overdue escalation threshold (hours) for GL-26 pending-ack aging diagnostics.",
    )
    parser.add_argument(
        "--backfill-handoff-now-utc",
        default="",
        help=(
            "Optional UTC timestamp passed to GL-24/GL-26 handoff stage for deterministic "
            "ack aging evaluation."
        ),
    )
    parser.add_argument(
        "--backfill-handoff-acknowledgements-report",
        default="",
        help=(
            "Optional operator acknowledgement report for GL-25 linkage closure. "
            "When provided, GL-24 handoff closure requires submission + acknowledgement match."
        ),
    )
    parser.add_argument("--trial-metrics-report-output", default=str(DEFAULT_TRIAL_METRICS_REPORT))
    parser.add_argument("--trial-metrics-summary-output", default=str(DEFAULT_TRIAL_METRICS_SUMMARY))
    parser.add_argument("--launch-readiness-output", default=str(DEFAULT_LAUNCH_READINESS_REPORT))
    parser.add_argument("--launch-readiness-summary-output", default=str(DEFAULT_LAUNCH_READINESS_SUMMARY))
    parser.add_argument("--release-switch-report", default=str(DEFAULT_RELEASE_SWITCH_REPORT))
    parser.add_argument("--current-status-doc", default=str(DEFAULT_CURRENT_STATUS_DOC))
    parser.add_argument(
        "--controlled-trial-run-report",
        default="",
        help=(
            "Run report path passed to launch-readiness gate security fallback. "
            "Defaults to first --run-report entry."
        ),
    )
    parser.add_argument("--agent-smoke-report", default=str(DEFAULT_AGENT_SMOKE_REPORT))
    parser.add_argument("--security-gate-report", default="")
    parser.add_argument("--doc-sync-report", default=str(DEFAULT_DOC_SYNC_REPORT))
    parser.add_argument("--operations-readiness-report", default=str(DEFAULT_OPERATIONS_READINESS_REPORT))
    parser.add_argument("--evidence-pack-output", default=str(DEFAULT_EVIDENCE_PACK))
    parser.add_argument("--run-doc-sync", dest="run_doc_sync", action="store_true", default=True)
    parser.add_argument("--no-run-doc-sync", dest="run_doc_sync", action="store_false")
    parser.add_argument("--minimum-complete-loops", type=int, default=10)
    parser.add_argument("--minimum-modalities", type=int, default=4)
    parser.add_argument("--release-decision", choices=("GO", "HOLD"), default="GO")
    parser.add_argument("--operator-cost-accepted", choices=("true", "false"), default="true")
    parser.add_argument("--max-evidence-age-hours", type=float, default=336.0)
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-blocker", action="store_true")
    parser.add_argument("--fail-on-hold", action="store_true")
    return parser.parse_args()


def _resolve_required_output_path(value: str, *, name: str) -> Path:
    cleaned = str(value or "").strip()
    if not cleaned or cleaned == "-":
        raise ValueError("%s cannot be empty or '-' for launch-evidence pipeline." % name)
    return Path(cleaned).resolve()


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _print_command_output(prefix: str, result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout.strip():
        print("%s stdout:\n%s" % (prefix, result.stdout.rstrip()))
    if result.stderr.strip():
        print("%s stderr:\n%s" % (prefix, result.stderr.rstrip()), file=sys.stderr)


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


def _format_no_loop_manifest_matches_message(
    *,
    manifest_dirs: list[Path],
    pattern: str,
    recursive: bool,
) -> str:
    directory_text = ", ".join(str(path) for path in manifest_dirs) if manifest_dirs else "none"
    normalized_pattern = str(pattern or "").strip() or "*.json"
    return (
        "no loop manifest JSON files matched explicit loop evidence input(s): "
        "directories=%s pattern=%s recursive=%s. "
        "Add at least one JSON manifest with top-level 'loops', or pass --run-report for run-report input."
        % (directory_text, normalized_pattern, str(bool(recursive)).lower())
    )


def _build_collection_command(args: argparse.Namespace, run_reports: list[Path], manifest_output: Path) -> list[str]:
    command = [
        sys.executable,
        str(REAL_LOOP_COLLECTION_SCRIPT),
    ]
    for path in run_reports:
        command.extend(["--run-report", str(path)])
    for value in args.loop_manifest:
        item = str(value).strip()
        if item:
            command.extend(["--loop-manifest", str(Path(item).resolve())])
    for value in args.loop_manifest_dir:
        item = str(value).strip()
        if item:
            command.extend(["--loop-manifest-dir", str(Path(item).resolve())])
    pattern = str(args.loop_manifest_pattern).strip()
    if pattern:
        command.extend(["--loop-manifest-pattern", pattern])
    if bool(args.loop_manifest_recursive):
        command.append("--loop-manifest-recursive")
    if bool(args.strict_loop_manifest_contract):
        command.append("--strict-loop-manifest-contract")
    command.extend(
        [
            "--output",
            str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
            "--summary-output",
            str(args.collection_summary_output),
            "--manifest-output",
            str(manifest_output),
            "--backfill-plan-output",
            str(args.backfill_plan_output),
            "--minimum-complete-loops",
            str(max(1, int(args.minimum_complete_loops))),
            "--minimum-modalities",
            str(max(1, int(args.minimum_modalities))),
            "--release-decision",
            str(args.release_decision).strip().upper(),
            "--operator-cost-accepted",
            str(args.operator_cost_accepted).strip().lower(),
        ]
    )
    if args.fail_on_blocker:
        command.append("--fail-on-blocker")
    return command


def _build_trial_metrics_command(args: argparse.Namespace, manifest_path: Path, report_output: Path) -> list[str]:
    return [
        sys.executable,
        str(TRIAL_METRICS_COLLECTOR_SCRIPT),
        "--manifest",
        str(manifest_path),
        "--output",
        str(report_output),
        "--summary-output",
        str(args.trial_metrics_summary_output),
        "--minimum-complete-loops",
        str(max(1, int(args.minimum_complete_loops))),
        "--minimum-modalities",
        str(max(1, int(args.minimum_modalities))),
    ]


def _build_backfill_execution_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_EXECUTION_SCRIPT),
        "--backfill-plan",
        str(Path(args.backfill_plan_output).resolve()),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(Path(args.backfill_execution_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_execution_summary_output).resolve()),
    ]


def _build_backfill_intake_actions_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_INTAKE_ACTIONS_SCRIPT),
        "--backfill-plan",
        str(Path(args.backfill_plan_output).resolve()),
        "--backfill-execution-report",
        str(Path(args.backfill_execution_output).resolve()),
        "--output",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_intake_actions_summary_output).resolve()),
        "--owner",
        str(args.backfill_intake_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_templates_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_SUBMISSION_TEMPLATES_SCRIPT),
        "--intake-actions-report",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--output",
        str(Path(args.backfill_submission_templates_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_submission_templates_summary_output).resolve()),
        "--manifest-template-output",
        str(Path(args.backfill_submission_manifest_template_output).resolve()),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_handoff_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(REAL_LOOP_BACKFILL_HANDOFF_SCRIPT),
        "--intake-actions-report",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(Path(args.backfill_handoff_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_handoff_summary_output).resolve()),
        "--owner",
        str(args.backfill_handoff_owner).strip() or "controlled-beta-ops",
        "--pending-ack-sla-hours",
        str(float(args.backfill_handoff_pending_ack_sla_hours)),
        "--pending-ack-overdue-hours",
        str(float(args.backfill_handoff_pending_ack_overdue_hours)),
    ]
    now_utc = str(args.backfill_handoff_now_utc).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    ack_report = str(args.backfill_handoff_acknowledgements_report).strip()
    if ack_report:
        command.extend(["--acknowledgements-report", str(Path(ack_report).resolve())])
    return command


def _build_backfill_handoff_escalations_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_HANDOFF_ESCALATIONS_SCRIPT),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--output",
        str(Path(args.backfill_handoff_escalations_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_handoff_escalations_summary_output).resolve()),
        "--owner",
        str(args.backfill_handoff_escalations_owner).strip() or "controlled-beta-ops",
    ]


def _build_launch_gate_command(
    args: argparse.Namespace,
    *,
    trial_metrics_report: Path,
    controlled_trial_run_report: Path,
    launch_readiness_output: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(LAUNCH_READINESS_GATE_SCRIPT),
        "--release-switch-report",
        str(Path(args.release_switch_report).resolve()),
        "--current-status-doc",
        str(Path(args.current_status_doc).resolve()),
        "--trial-metrics-report",
        str(trial_metrics_report),
        "--controlled-trial-run-report",
        str(controlled_trial_run_report),
        "--agent-smoke-report",
        str(Path(args.agent_smoke_report).resolve()),
        "--doc-sync-report",
        str(Path(args.doc_sync_report).resolve()),
        "--operations-readiness-report",
        str(Path(args.operations_readiness_report).resolve()),
        "--minimum-complete-loops",
        str(max(1, int(args.minimum_complete_loops))),
        "--minimum-modalities",
        str(max(1, int(args.minimum_modalities))),
        "--max-evidence-age-hours",
        str(float(args.max_evidence_age_hours)),
        "--output",
        str(launch_readiness_output),
        "--summary-output",
        str(args.launch_readiness_summary_output),
    ]
    security_gate_report_value = str(args.security_gate_report).strip()
    if security_gate_report_value:
        command.extend(["--security-gate-report", str(Path(security_gate_report_value).resolve())])
    command.append("--run-doc-sync" if args.run_doc_sync else "--no-run-doc-sync")
    if args.print_json:
        command.append("--print-json")
    if args.print_summary:
        command.append("--print-summary")
    return command


def _build_evidence_pack(
    *,
    args: argparse.Namespace,
    collection_report: dict[str, Any],
    trial_metrics_report: dict[str, Any],
    launch_readiness_report: dict[str, Any],
    backfill_execution_report: dict[str, Any],
    backfill_intake_actions_report: dict[str, Any],
    backfill_submission_templates_report: dict[str, Any],
    backfill_handoff_report: dict[str, Any],
    backfill_handoff_escalations_report: dict[str, Any],
    run_report_paths: list[Path],
    loop_manifest_paths: list[Path],
) -> dict[str, Any]:
    trial_metrics = trial_metrics_report.get("trial_metrics", {})
    if not isinstance(trial_metrics, dict):
        trial_metrics = {}
    launch_gate_evidence = trial_metrics.get("launch_gate_evidence", {})
    if not isinstance(launch_gate_evidence, dict):
        launch_gate_evidence = {}
    safety = trial_metrics.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    collection_alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(collection_alignment, dict):
        collection_alignment = {}
    backfill_slot_counts = backfill_execution_report.get("slot_counts", {})
    if not isinstance(backfill_slot_counts, dict):
        backfill_slot_counts = {}
    backfill_submission_backed_slot_counts = backfill_execution_report.get("submission_backed_slot_counts", {})
    if not isinstance(backfill_submission_backed_slot_counts, dict):
        backfill_submission_backed_slot_counts = {}
    backfill_submission_linkage_counts = backfill_execution_report.get("submission_linkage_counts", {})
    if not isinstance(backfill_submission_linkage_counts, dict):
        backfill_submission_linkage_counts = {}
    backfill_coverage_delta = backfill_execution_report.get("coverage_delta", {})
    if not isinstance(backfill_coverage_delta, dict):
        backfill_coverage_delta = {}
    backfill_intake_action_counts = backfill_intake_actions_report.get("action_counts", {})
    if not isinstance(backfill_intake_action_counts, dict):
        backfill_intake_action_counts = {}
    backfill_submission_template_counts = backfill_submission_templates_report.get("template_counts", {})
    if not isinstance(backfill_submission_template_counts, dict):
        backfill_submission_template_counts = {}
    backfill_submission_action_counts = backfill_submission_templates_report.get("action_counts", {})
    if not isinstance(backfill_submission_action_counts, dict):
        backfill_submission_action_counts = {}
    backfill_handoff_counts = backfill_handoff_report.get("queue_item_counts", {})
    if not isinstance(backfill_handoff_counts, dict):
        backfill_handoff_counts = {}
    backfill_handoff_submission_linkage_snapshot = backfill_handoff_report.get("submission_linkage_snapshot", {})
    if not isinstance(backfill_handoff_submission_linkage_snapshot, dict):
        backfill_handoff_submission_linkage_snapshot = {}
    backfill_handoff_ack_snapshot = backfill_handoff_report.get("acknowledgement_snapshot", {})
    if not isinstance(backfill_handoff_ack_snapshot, dict):
        backfill_handoff_ack_snapshot = {}
    backfill_handoff_ack_sla_snapshot = backfill_handoff_report.get("acknowledgement_sla_snapshot", {})
    if not isinstance(backfill_handoff_ack_sla_snapshot, dict):
        backfill_handoff_ack_sla_snapshot = {}
    backfill_handoff_escalation_counts = backfill_handoff_escalations_report.get("escalation_counts", {})
    if not isinstance(backfill_handoff_escalation_counts, dict):
        backfill_handoff_escalation_counts = {}
    backfill_handoff_escalation_exports = backfill_handoff_escalations_report.get("escalation_exports", {})
    if not isinstance(backfill_handoff_escalation_exports, dict):
        backfill_handoff_escalation_exports = {}
    failed_checks = launch_readiness_report.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = []
    decision = str(launch_readiness_report.get("decision", "HOLD")).strip().upper() or "HOLD"

    return {
        "schema_version": "real_trial_launch_evidence_pack.v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stage": "controlled_external_beta",
        "launch_decision": decision,
        "ready_for_controlled_beta": decision == "READY_FOR_CONTROLLED_BETA",
        "ready_for_ga_review": decision == "READY_FOR_GA_REVIEW",
        "ready_for_platform_beta": decision == "READY_FOR_PLATFORM_BETA",
        "evidence_paths": {
            "collection_report": str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
            "collection_summary": str(Path(args.collection_summary_output).resolve()),
            "real_trial_manifest": str(_resolve_required_output_path(args.real_trial_manifest_output, name="real-trial-manifest-output")),
            "real_trial_backfill_plan": str(Path(args.backfill_plan_output).resolve()),
            "real_trial_backfill_execution_report": str(Path(args.backfill_execution_output).resolve()),
            "real_trial_backfill_execution_summary": str(Path(args.backfill_execution_summary_output).resolve()),
            "real_trial_backfill_intake_actions_report": str(Path(args.backfill_intake_actions_output).resolve()),
            "real_trial_backfill_intake_actions_summary": str(Path(args.backfill_intake_actions_summary_output).resolve()),
            "real_trial_backfill_submission_templates_report": str(
                Path(args.backfill_submission_templates_output).resolve()
            ),
            "real_trial_backfill_submission_templates_summary": str(
                Path(args.backfill_submission_templates_summary_output).resolve()
            ),
            "real_trial_backfill_submission_manifest_template": str(
                Path(args.backfill_submission_manifest_template_output).resolve()
            ),
            "real_trial_backfill_handoff_report": str(Path(args.backfill_handoff_output).resolve()),
            "real_trial_backfill_handoff_summary": str(Path(args.backfill_handoff_summary_output).resolve()),
            "real_trial_backfill_handoff_acknowledgements_report": str(
                Path(args.backfill_handoff_acknowledgements_report).resolve()
            )
            if str(args.backfill_handoff_acknowledgements_report).strip()
            else "",
            "real_trial_backfill_handoff_escalations_report": str(
                Path(args.backfill_handoff_escalations_output).resolve()
            ),
            "real_trial_backfill_handoff_escalations_summary": str(
                Path(args.backfill_handoff_escalations_summary_output).resolve()
            ),
            "trial_metrics_report": str(_resolve_required_output_path(args.trial_metrics_report_output, name="trial-metrics-report-output")),
            "trial_metrics_summary": str(Path(args.trial_metrics_summary_output).resolve()),
            "launch_readiness_report": str(_resolve_required_output_path(args.launch_readiness_output, name="launch-readiness-output")),
            "launch_readiness_summary": str(Path(args.launch_readiness_summary_output).resolve()),
        },
        "input_sources": {
            "run_report_paths": [str(path) for path in run_report_paths],
            "loop_manifest_paths": collection_report.get("source_loop_manifest_paths", []),
            "input_report_count": len(run_report_paths),
            "input_loop_manifest_count": int(collection_report.get("input_loop_manifest_count", 0) or 0),
            "ingested_loop_manifest_count": int(collection_report.get("ingested_loop_manifest_count", 0) or 0),
            "skipped_non_loop_manifest_count": int(
                collection_report.get("skipped_non_loop_manifest_count", 0) or 0
            ),
            "skipped_non_loop_manifest_paths": collection_report.get("skipped_non_loop_manifest_paths", []),
            "input_loop_manifest_dir_count": int(collection_report.get("input_loop_manifest_dir_count", 0) or 0),
            "loop_manifest_dirs": collection_report.get("source_loop_manifest_dirs", []),
            "duplicate_resolution_count": int(collection_report.get("duplicate_resolution_count", 0) or 0),
            "duplicate_resolution_records": collection_report.get("duplicate_resolution_records", []),
        },
        "evidence_classification": {
            "evidence_origin_counts": collection_report.get("evidence_origin_counts", {}),
            "launch_gate_ineligible_reason_counts": collection_report.get("launch_gate_ineligible_reason_counts", {}),
            "total_complete_loop_count": int(trial_metrics.get("complete_loop_count", 0) or 0),
            "total_complete_modalities": trial_metrics.get("complete_modalities", []),
            "launch_gate_eligible_complete_loop_count": int(launch_gate_evidence.get("complete_loop_count", 0) or 0),
            "launch_gate_eligible_complete_modalities": launch_gate_evidence.get("complete_modalities", []),
            "target_launch_modalities": collection_alignment.get("target_launch_modalities", []),
            "covered_target_launch_modalities": collection_alignment.get("covered_target_launch_modalities", []),
            "missing_target_launch_modalities": collection_alignment.get("missing_target_launch_modalities", []),
            "recommended_next_modalities": collection_alignment.get("recommended_next_modalities", []),
            "launch_gate_eligible_complete_loop_count_by_modality": collection_alignment.get(
                "launch_gate_eligible_complete_loop_count_by_modality", {}
            ),
            "target_launch_modality_loop_counts": collection_alignment.get("target_launch_modality_loop_counts", {}),
            "real_evidence_missing_source_trace_count": int(
                launch_gate_evidence.get("real_evidence_missing_source_trace_count", 0) or 0
            ),
            "real_evidence_missing_review_trace_count": int(
                launch_gate_evidence.get("real_evidence_missing_review_trace_count", 0) or 0
            ),
            "collection_program_status": str(collection_alignment.get("program_status", "unknown")),
            "collection_blockers": collection_alignment.get("blockers", []),
            "missing_complete_loops_to_threshold": int(
                collection_alignment.get("missing_complete_loops_to_threshold", 0) or 0
            ),
            "missing_modalities_to_threshold": int(
                collection_alignment.get("missing_modalities_to_threshold", 0) or 0
            ),
            "recommended_backfill_slot_count": int(collection_alignment.get("recommended_backfill_slot_count", 0) or 0),
            "recommended_backfill_slots": collection_alignment.get("recommended_backfill_slots", []),
            "backfill_execution_status": str(backfill_execution_report.get("execution_status", "unknown")),
            "backfill_execution_fulfilled_slot_count": int(backfill_slot_counts.get("fulfilled_slot_count", 0) or 0),
            "backfill_execution_remaining_slot_count": int(backfill_slot_counts.get("remaining_slot_count", 0) or 0),
            "backfill_execution_submission_backed_status": str(
                backfill_execution_report.get("submission_backed_execution_status", "unknown")
            ),
            "backfill_execution_submission_backed_fulfilled_slot_count": int(
                backfill_submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count", 0) or 0
            ),
            "backfill_execution_submission_backed_remaining_slot_count": int(
                backfill_submission_backed_slot_counts.get("submission_backed_remaining_slot_count", 0) or 0
            ),
            "backfill_execution_fulfilled_without_submission_linkage_count": int(
                backfill_submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count", 0) or 0
            ),
            "backfill_execution_submission_linked_without_modality_delta_count": int(
                backfill_submission_backed_slot_counts.get("submission_linked_without_modality_delta_count", 0) or 0
            ),
            "backfill_execution_gained_target_launch_modality_loop_counts": backfill_coverage_delta.get(
                "gained_target_launch_modality_loop_counts",
                {},
            ),
            "backfill_execution_submission_linked_slot_count": int(
                backfill_submission_linkage_counts.get("submission_linked_slot_count", 0) or 0
            ),
            "backfill_execution_submission_slot_linked_count": int(
                backfill_submission_linkage_counts.get("slot_linked_count", 0) or 0
            ),
            "backfill_execution_submission_action_linked_count": int(
                backfill_submission_linkage_counts.get("action_linked_count", 0) or 0
            ),
            "backfill_execution_unmatched_submission_linkage_count": int(
                backfill_submission_linkage_counts.get("unmatched_submission_linkage_count", 0) or 0
            ),
            "backfill_execution_submission_linkage_records": backfill_execution_report.get(
                "submission_linkage_records",
                [],
            ),
            "backfill_execution_unmatched_submission_linkages": backfill_execution_report.get(
                "unmatched_submission_linkages",
                [],
            ),
            "backfill_intake_status": str(backfill_intake_actions_report.get("intake_status", "unknown")),
            "backfill_intake_total_action_count": int(backfill_intake_action_counts.get("total_actions", 0) or 0),
            "backfill_intake_pending_action_count": int(backfill_intake_action_counts.get("pending_action_count", 0) or 0),
            "backfill_intake_closed_action_count": int(backfill_intake_action_counts.get("closed_action_count", 0) or 0),
            "backfill_intake_owner": str(args.backfill_intake_owner).strip() or "controlled-beta-ops",
            "backfill_submission_template_status": str(
                backfill_submission_templates_report.get("template_status", "unknown")
            ),
            "backfill_submission_template_total_action_count": int(
                backfill_submission_action_counts.get("total_action_count", 0) or 0
            ),
            "backfill_submission_template_pending_action_count": int(
                backfill_submission_action_counts.get("pending_action_count", 0) or 0
            ),
            "backfill_submission_template_generated_count": int(
                backfill_submission_template_counts.get("generated_template_count", 0) or 0
            ),
            "backfill_submission_template_missing_count": int(
                backfill_submission_template_counts.get("missing_template_action_count", 0) or 0
            ),
            "backfill_submission_template_owner": str(args.backfill_submission_owner).strip()
            or "controlled-beta-ops",
            "backfill_submission_template_missing_actions": backfill_submission_templates_report.get(
                "missing_template_actions",
                [],
            ),
            "backfill_handoff_status": str(backfill_handoff_report.get("handoff_status", "unknown")),
            "backfill_handoff_total_queue_item_count": int(
                backfill_handoff_counts.get("total_queue_item_count", 0) or 0
            ),
            "backfill_handoff_open_queue_item_count": int(
                backfill_handoff_counts.get("open_queue_item_count", 0) or 0
            ),
            "backfill_handoff_submission_linked_pending_ack_count": int(
                backfill_handoff_counts.get("submission_linked_pending_ack_count", 0) or 0
            ),
            "backfill_handoff_closure_acknowledged_count": int(
                backfill_handoff_counts.get("closure_acknowledged_count", 0) or 0
            ),
            "backfill_handoff_owner": str(args.backfill_handoff_owner).strip() or "controlled-beta-ops",
            "backfill_handoff_submission_linkage_strategy_counts": backfill_handoff_submission_linkage_snapshot.get(
                "linkage_strategy_counts",
                {},
            ),
            "backfill_handoff_submission_unlinked_count": int(
                backfill_handoff_submission_linkage_snapshot.get("unlinked_submission_count", 0) or 0
            ),
            "backfill_handoff_submission_unlinked_records": backfill_handoff_submission_linkage_snapshot.get(
                "unlinked_submissions",
                [],
            ),
            "backfill_handoff_acknowledgement_input_count": int(
                backfill_handoff_ack_snapshot.get("input_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_valid_count": int(
                backfill_handoff_ack_snapshot.get("valid_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_invalid_count": int(
                backfill_handoff_ack_snapshot.get("invalid_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_invalid_records": backfill_handoff_ack_snapshot.get(
                "invalid_acknowledgement_records",
                [],
            ),
            "backfill_handoff_acknowledgement_sla_status": str(
                backfill_handoff_ack_sla_snapshot.get("acknowledgement_sla_status", "unknown")
            ),
            "backfill_handoff_acknowledgement_sla_hours": float(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_sla_hours", 0.0) or 0.0
            ),
            "backfill_handoff_acknowledgement_overdue_hours": float(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_overdue_hours", 0.0) or 0.0
            ),
            "backfill_handoff_acknowledgement_sla_evaluation_timestamp_utc": str(
                backfill_handoff_ack_sla_snapshot.get("evaluation_timestamp_utc", "")
            ),
            "backfill_handoff_acknowledgement_within_sla_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_within_sla_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_sla_breached_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_sla_breached_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_overdue_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_overdue_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_tracking_incomplete_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_missing_reference_timestamp_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_sla_breached_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_sla_breached_queue_items",
                [],
            ),
            "backfill_handoff_acknowledgement_overdue_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_overdue_queue_items",
                [],
            ),
            "backfill_handoff_acknowledgement_tracking_incomplete_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_tracking_incomplete_queue_items",
                [],
            ),
            "backfill_handoff_escalation_status": str(
                backfill_handoff_escalations_report.get("escalation_status", "unknown")
            ),
            "backfill_handoff_escalation_owner": str(
                backfill_handoff_escalations_report.get("owner", "")
            )
            or (str(args.backfill_handoff_escalations_owner).strip() or "controlled-beta-ops"),
            "backfill_handoff_escalation_total_item_count": int(
                backfill_handoff_escalation_counts.get("total_escalation_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_sla_breached_item_count": int(
                backfill_handoff_escalation_counts.get("sla_breached_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_overdue_item_count": int(
                backfill_handoff_escalation_counts.get("overdue_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_tracking_incomplete_item_count": int(
                backfill_handoff_escalation_counts.get("tracking_incomplete_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_sla_breached_items": backfill_handoff_escalation_exports.get(
                "sla_breached_items",
                [],
            ),
            "backfill_handoff_escalation_overdue_items": backfill_handoff_escalation_exports.get(
                "overdue_items",
                [],
            ),
            "backfill_handoff_escalation_tracking_incomplete_items": backfill_handoff_escalation_exports.get(
                "tracking_incomplete_items",
                [],
            ),
        },
        "safety_summary": {
            "unreviewed_published_count": int(safety.get("unreviewed_published_count", 0) or 0),
            "critical_secret_or_pii_leak_count": int(safety.get("critical_secret_or_pii_leak_count", 0) or 0),
            "high_severity_incident_count": int(safety.get("high_severity_incident_count", 0) or 0),
        },
        "gate_summary": {
            "failed_checks": failed_checks,
            "blocking_check_count": len(failed_checks),
        },
        "policy_notes": [
            "This pack summarizes controlled external Beta evidence only.",
            "Fixture or synthetic loops are not launch-gate-eligible real evidence.",
            "No GA claim is allowed unless launch_readiness decision and gate checks support it.",
        ],
    }


def main() -> int:
    args = _parse_args()
    run_report_values = [str(value).strip() for value in args.run_report if str(value).strip()]
    loop_manifest_values = [str(value).strip() for value in args.loop_manifest if str(value).strip()]
    loop_manifest_dir_values = [str(value).strip() for value in args.loop_manifest_dir if str(value).strip()]
    run_report_paths = [Path(value).resolve() for value in run_report_values]
    try:
        loop_manifest_paths, loop_manifest_dirs = _resolve_loop_manifest_paths(
            explicit_paths=loop_manifest_values,
            manifest_dirs=loop_manifest_dir_values,
            pattern=str(args.loop_manifest_pattern),
            recursive=bool(args.loop_manifest_recursive),
        )
    except ValueError as exc:
        print("Real-trial launch evidence pipeline failed: %s" % exc, file=sys.stderr)
        return 2
    if (loop_manifest_values or loop_manifest_dir_values) and not loop_manifest_paths:
        print(
            "Real-trial launch evidence pipeline failed: %s"
            % _format_no_loop_manifest_matches_message(
                manifest_dirs=loop_manifest_dirs,
                pattern=str(args.loop_manifest_pattern),
                recursive=bool(args.loop_manifest_recursive),
            ),
            file=sys.stderr,
        )
        return 2
    if not run_report_paths and not loop_manifest_paths and not loop_manifest_dirs:
        run_report_paths = [DEFAULT_RUN_REPORT]
    missing_inputs = [path for path in run_report_paths if not path.is_file()]
    missing_inputs.extend(path for path in loop_manifest_paths if not path.is_file())
    if missing_inputs:
        print(
            "Real-trial launch evidence pipeline failed: missing loop evidence input(s): %s"
            % ", ".join(str(path) for path in missing_inputs),
            file=sys.stderr,
        )
        return 2

    try:
        manifest_output = _resolve_required_output_path(
            args.real_trial_manifest_output,
            name="real-trial-manifest-output",
        )
        trial_metrics_output = _resolve_required_output_path(
            args.trial_metrics_report_output,
            name="trial-metrics-report-output",
        )
        launch_readiness_output = _resolve_required_output_path(
            args.launch_readiness_output,
            name="launch-readiness-output",
        )
        evidence_pack_output = _resolve_required_output_path(
            args.evidence_pack_output,
            name="evidence-pack-output",
        )
    except ValueError as exc:
        print("Real-trial launch evidence pipeline failed: %s" % exc, file=sys.stderr)
        return 2

    controlled_trial_run_report_value = str(args.controlled_trial_run_report).strip()
    controlled_trial_run_report = (
        Path(controlled_trial_run_report_value).resolve()
        if controlled_trial_run_report_value
        else (run_report_paths[0] if run_report_paths else DEFAULT_RUN_REPORT)
    )

    collection_command = _build_collection_command(args, run_report_paths, manifest_output)
    collection_result = _run_command(collection_command)
    _print_command_output("real-trial-loop-collection", collection_result)
    if collection_result.returncode != 0:
        return collection_result.returncode

    trial_metrics_command = _build_trial_metrics_command(args, manifest_output, trial_metrics_output)
    trial_metrics_result = _run_command(trial_metrics_command)
    _print_command_output("trial-metrics-collector", trial_metrics_result)
    if trial_metrics_result.returncode != 0:
        return trial_metrics_result.returncode

    backfill_execution_command = _build_backfill_execution_command(args)
    backfill_execution_result = _run_command(backfill_execution_command)
    _print_command_output("real-trial-backfill-execution", backfill_execution_result)
    if backfill_execution_result.returncode != 0:
        return backfill_execution_result.returncode

    backfill_intake_actions_command = _build_backfill_intake_actions_command(args)
    backfill_intake_actions_result = _run_command(backfill_intake_actions_command)
    _print_command_output("real-trial-backfill-intake-actions", backfill_intake_actions_result)
    if backfill_intake_actions_result.returncode != 0:
        return backfill_intake_actions_result.returncode

    backfill_submission_templates_command = _build_backfill_submission_templates_command(args)
    backfill_submission_templates_result = _run_command(backfill_submission_templates_command)
    _print_command_output("real-trial-backfill-submission-templates", backfill_submission_templates_result)
    if backfill_submission_templates_result.returncode != 0:
        return backfill_submission_templates_result.returncode

    backfill_handoff_command = _build_backfill_handoff_command(args)
    backfill_handoff_result = _run_command(backfill_handoff_command)
    _print_command_output("real-trial-backfill-handoff", backfill_handoff_result)
    if backfill_handoff_result.returncode != 0:
        return backfill_handoff_result.returncode

    backfill_handoff_escalations_command = _build_backfill_handoff_escalations_command(args)
    backfill_handoff_escalations_result = _run_command(backfill_handoff_escalations_command)
    _print_command_output("real-trial-backfill-handoff-escalations", backfill_handoff_escalations_result)
    if backfill_handoff_escalations_result.returncode != 0:
        return backfill_handoff_escalations_result.returncode

    launch_gate_command = _build_launch_gate_command(
        args,
        trial_metrics_report=trial_metrics_output,
        controlled_trial_run_report=controlled_trial_run_report,
        launch_readiness_output=launch_readiness_output,
    )
    launch_gate_result = _run_command(launch_gate_command)
    _print_command_output("launch-readiness-gate", launch_gate_result)
    if launch_gate_result.returncode != 0:
        return launch_gate_result.returncode

    try:
        collection_report = _read_json(_resolve_required_output_path(args.collection_report_output, name="collection-report-output"))
        trial_metrics_report = _read_json(trial_metrics_output)
        launch_readiness_report = _read_json(launch_readiness_output)
        backfill_execution_report = _read_json(Path(args.backfill_execution_output).resolve())
        backfill_intake_actions_report = _read_json(Path(args.backfill_intake_actions_output).resolve())
        backfill_submission_templates_report = _read_json(Path(args.backfill_submission_templates_output).resolve())
        backfill_handoff_report = _read_json(Path(args.backfill_handoff_output).resolve())
        backfill_handoff_escalations_report = _read_json(Path(args.backfill_handoff_escalations_output).resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real-trial launch evidence pipeline failed while reading reports: %s" % exc, file=sys.stderr)
        return 2

    try:
        evidence_pack = _build_evidence_pack(
            args=args,
            collection_report=collection_report,
            trial_metrics_report=trial_metrics_report,
            launch_readiness_report=launch_readiness_report,
            backfill_execution_report=backfill_execution_report,
            backfill_intake_actions_report=backfill_intake_actions_report,
            backfill_submission_templates_report=backfill_submission_templates_report,
            backfill_handoff_report=backfill_handoff_report,
            backfill_handoff_escalations_report=backfill_handoff_escalations_report,
            run_report_paths=run_report_paths,
            loop_manifest_paths=loop_manifest_paths,
        )
        _write_json(evidence_pack_output, evidence_pack)
        print("Real-trial launch evidence pack written: %s" % evidence_pack_output)
    except (OSError, ValueError) as exc:
        print("Real-trial launch evidence pipeline failed while writing evidence pack: %s" % exc, file=sys.stderr)
        return 2

    collection_alignment = collection_report.get("launch_gate_alignment", {})
    trial_metrics = trial_metrics_report.get("trial_metrics", {})
    launch_gate_evidence = trial_metrics.get("launch_gate_evidence", {}) if isinstance(trial_metrics, dict) else {}
    decision = str(launch_readiness_report.get("decision", "HOLD")).strip().upper() or "HOLD"
    failed_checks = launch_readiness_report.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = []

    print(
        "Real-trial launch evidence pipeline decision=%s collection_status=%s real_eligible_complete=%s modalities=%s failed_checks=%s"
        % (
            decision,
            str(collection_alignment.get("program_status", "unknown")),
            int(launch_gate_evidence.get("complete_loop_count", 0) or 0),
            len(launch_gate_evidence.get("complete_modalities", []))
            if isinstance(launch_gate_evidence.get("complete_modalities", []), list)
            else 0,
            "none" if not failed_checks else ",".join(str(item) for item in failed_checks),
        )
    )
    if args.fail_on_hold and decision == "HOLD":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
