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
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-roadmap-extension-validation-plan.json'
)
DEFAULT_STAGES = (
    'retrieval_layer',
    'lifecycle_engine',
    'publication_expansion',
    'review_queue_surface',
)
ALL_STAGES = tuple(DEFAULT_STAGES)


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print a roadmap-extension validation command pack for Linux.',
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
        help='Validation stages to include. Defaults to full roadmap-extension command pack.',
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


def _build_stage_map(*, python_cmd: list[str]) -> dict[str, StageSpec]:
    return {
        'retrieval_layer': StageSpec(
            name='retrieval_layer',
            description='Validate retrieval abstraction and backend-routing behavior.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_similarity_retrieval.SimilarityRetrievalTests',
            ],
        ),
        'lifecycle_engine': StageSpec(
            name='lifecycle_engine',
            description='Validate lifecycle decision routing for new/revise/merge/supersede flows.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_lifecycle_decision_engine.LifecycleDecisionEngineTests',
            ],
        ),
        'publication_expansion': StageSpec(
            name='publication_expansion',
            description='Validate publication multi-view builders and orchestrator harmonization.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_publication_builder.PublicationBuilderTests',
                'tests.test_publication_orchestrator_split.PublicationHarmonizerTests',
                'tests.test_publication_orchestrator_split.PublicationOrchestratorTests',
            ],
        ),
        'review_queue_surface': StageSpec(
            name='review_queue_surface',
            description='Validate review queue repository/service/api operation surface.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_review_queue_repository.ReviewQueueRepositoryTests',
                'tests.test_review_queue_integration.ReviewQueueIntegrationTests',
                'tests.test_api_review_queue.ApiReviewQueueEndpointTests',
            ],
        ),
    }


def _build_plan(stage_specs: list[StageSpec]) -> dict[str, Any]:
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'stage_count': len(stage_specs),
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

    stage_map = _build_stage_map(python_cmd=python_cmd)
    stage_specs = [stage_map[name] for name in args.stages]
    _print_plan(stage_specs)

    plan_payload = _build_plan(stage_specs)
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
