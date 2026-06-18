from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.trial_metrics import (  # noqa: E402
    TrialMetricsCollector,
    TrialSuccessCriteriaThresholds,
    render_trial_metrics_markdown_summary,
)

DEFAULT_MANIFEST_PATH = (
    REPO_ROOT / "docs" / "current" / "status" / "baselines" / "trial-metrics" / "trial-metrics-manifest.template.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "current" / "status" / "baselines" / "trial-metrics" / "trial-metrics-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT / "docs" / "current" / "status" / "baselines" / "trial-metrics" / "trial-metrics-summary.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate controlled-trial loop metrics and evaluate GA discussion conditions "
            "from docs/working/status/2026-05-18-controlled-business-trial-iteration.md."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Trial metrics manifest path.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='JSON report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Markdown summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print full JSON report to stdout.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print markdown summary to stdout.",
    )
    parser.add_argument(
        "--fail-on-ga-blocker",
        action="store_true",
        help="Exit with code 1 when any critical GA condition fails.",
    )
    parser.add_argument(
        "--minimum-complete-loops",
        type=int,
        default=10,
        help="Minimum complete loops required by success criteria.",
    )
    parser.add_argument(
        "--minimum-modalities",
        type=int,
        default=4,
        help="Minimum modality coverage required by success criteria.",
    )
    parser.add_argument(
        "--minimum-approval-rate-after-one-revision",
        type=float,
        default=0.8,
        help="Minimum reviewer approval rate after <=1 revision.",
    )
    parser.add_argument(
        "--maximum-median-reviewer-edit-distance-pct",
        type=float,
        default=25.0,
        help="Maximum median reviewer edit distance percentage.",
    )
    parser.add_argument(
        "--minimum-agent-smoke-success-rate",
        type=float,
        default=0.8,
        help="Minimum approved-skill agent smoke success rate.",
    )
    parser.add_argument(
        "--maximum-provider-failure-rate",
        type=float,
        default=0.05,
        help="Maximum provider/runtime failure rate.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object.")
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(args.output).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(args.summary_output).resolve()

    thresholds = TrialSuccessCriteriaThresholds(
        minimum_complete_loops=max(1, int(args.minimum_complete_loops)),
        minimum_modalities=max(1, int(args.minimum_modalities)),
        minimum_approval_rate_after_one_revision=max(
            0.0, min(1.0, float(args.minimum_approval_rate_after_one_revision))
        ),
        maximum_median_reviewer_edit_distance_pct=max(0.0, float(args.maximum_median_reviewer_edit_distance_pct)),
        minimum_agent_smoke_success_rate=max(0.0, min(1.0, float(args.minimum_agent_smoke_success_rate))),
        maximum_provider_failure_rate=max(0.0, min(1.0, float(args.maximum_provider_failure_rate))),
    )
    collector = TrialMetricsCollector(thresholds=thresholds)

    try:
        payload = _read_json(manifest_path)
        report = collector.collect(payload)
        summary_markdown = render_trial_metrics_markdown_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Trial metrics collection failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Trial metrics report written: %s" % output_path)

    if summary_path is not None:
        _write_text(summary_path, summary_markdown)
        print("Trial metrics summary written: %s" % summary_path)

    criteria = report.get("success_criteria", {})
    print(
        "Trial metrics loops=%s complete=%s modalities=%s status=%s blockers=%s"
        % (
            report.get("trial_metrics", {}).get("loop_count", 0),
            report.get("trial_metrics", {}).get("complete_loop_count", 0),
            len(report.get("trial_metrics", {}).get("complete_modalities", [])),
            report.get("overall_status", "unknown"),
            "yes" if bool(report.get("ga_discussion_blocked")) else "no",
        )
    )

    failed_conditions = criteria.get("failed_conditions", [])
    if failed_conditions:
        print("Failed conditions: %s" % ", ".join(str(item.get("id", "")) for item in failed_conditions))
    else:
        print("Failed conditions: none")

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary_markdown.rstrip())

    if args.fail_on_ga_blocker and bool(report.get("ga_discussion_blocked")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
