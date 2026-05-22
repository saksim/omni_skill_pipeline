from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from omni_skill_pipeline.exporters import AgentSkillExporter
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    AgentSkillTarget,
    CorpusDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    PublicationType,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service
from omni_skill_pipeline.validation import validate_skill_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Omni Skill Pipeline CLI')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    text_parser = subparsers.add_parser('distill-text', help='Distill a text source')
    text_parser.add_argument('--title', help='Optional skill title')
    text_parser.add_argument('--file', dest='file_path', help='Text file path')
    text_parser.add_argument('--content', help='Inline text content')
    _attach_goal_args(text_parser)

    audio_parser = subparsers.add_parser('distill-audio', help='Distill an audio source')
    audio_parser.add_argument('--title', help='Optional skill title')
    audio_parser.add_argument('--audio-path', help='Audio file path')
    audio_parser.add_argument('--transcript', help='Inline transcript')
    audio_parser.add_argument('--transcript-path', help='Transcript sidecar path')
    audio_parser.add_argument('--language', help='ASR language hint')
    audio_parser.add_argument('--prompt', help='ASR prompt or glossary hint')
    _attach_goal_args(audio_parser)

    image_parser = subparsers.add_parser('distill-image', help='Distill an image source')
    image_parser.add_argument('--image-path', required=True)
    image_parser.add_argument('--title', help='Optional skill title')
    _attach_goal_args(image_parser)

    tabular_parser = subparsers.add_parser('distill-tabular', help='Distill a structured table or time series')
    tabular_parser.add_argument('--file', dest='file_path', required=True)
    tabular_parser.add_argument('--title', help='Optional skill title')
    tabular_parser.add_argument('--time-column')
    tabular_parser.add_argument('--value-column', dest='value_columns', action='append')
    tabular_parser.add_argument('--entity-column', dest='entity_columns', action='append')
    tabular_parser.add_argument('--max-series', type=int, default=6)
    _attach_goal_args(tabular_parser)

    video_parser = subparsers.add_parser('distill-video', help='Distill a video source')
    video_parser.add_argument('--video-path', required=True)
    video_parser.add_argument('--title', help='Optional skill title')
    video_parser.add_argument('--transcript', help='Optional inline transcript')
    video_parser.add_argument('--transcript-path', help='Optional transcript sidecar path')
    video_parser.add_argument('--language', help='ASR language hint')
    video_parser.add_argument('--prompt', help='ASR prompt or glossary hint')
    video_parser.add_argument('--keyframe-interval-seconds', type=int)
    video_parser.add_argument('--max-keyframes', type=int)
    video_parser.add_argument('--scene-threshold', type=float)
    video_parser.add_argument('--dedupe-distance', type=int)
    _attach_goal_args(video_parser)

    corpus_parser = subparsers.add_parser('distill-corpus', help='Distill a multi-asset corpus')
    corpus_parser.add_argument('--name', help='Optional corpus name')
    corpus_parser.add_argument(
        '--asset',
        action='append',
        default=[],
        help='Corpus asset spec. Use "modality=source_uri" or JSON object string. Repeat for multi-asset input.',
    )
    corpus_parser.add_argument('--tag', dest='tags', action='append', default=[])
    corpus_parser.add_argument('--metadata-json', default='')
    payload_group = corpus_parser.add_mutually_exclusive_group()
    payload_group.add_argument('--payload-file', help='Path to JSON payload matching CorpusDistillRequest.')
    payload_group.add_argument('--payload-json', help='Inline JSON payload matching CorpusDistillRequest.')
    corpus_parser.add_argument(
        '--publication',
        default=PublicationType.SKILL_MARKDOWN.value,
        help='Preferred publication type to print (skill_markdown/skill_json/checklist_json/decision_tree_json).',
    )
    corpus_parser.add_argument(
        '--show-publications',
        action='store_true',
        help='Print available publication types and review status.',
    )
    _attach_goal_args(corpus_parser)

    export_parser = subparsers.add_parser('export-skill', help='Export an agent skill package from an existing bundle')
    export_parser.add_argument('--bundle', required=True, help='Path to a distillation bundle.json file.')
    export_parser.add_argument(
        '--target',
        default=AgentSkillTarget.PORTABLE.value,
        help='Export target (codex/claude-code/opencode/portable/all).',
    )
    export_parser.add_argument(
        '--output-root',
        default='.',
        help='Root directory where target package layouts are written.',
    )
    validate_parser = subparsers.add_parser(
        'validate-skill',
        help='Validate an exported skill package for controlled-trial usability/safety rules',
    )
    validate_parser.add_argument('--package', required=True, help='Exported package directory path.')
    validate_parser.add_argument('--max-lines', type=int, default=500, help='Max allowed SKILL.md line count.')

    subparsers.add_parser('show-template', help='Print SKILL template path and content')
    return parser


def _attach_goal_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--goal-type', default='build_skill')
    parser.add_argument('--audience', default='self')
    parser.add_argument('--rigor', default='draft')
    parser.add_argument('--granularity', default='task')
    parser.add_argument('--domain', default='general')


def _goal_from_args(args: argparse.Namespace) -> DistillGoal:
    return DistillGoal.from_dict(
        {
            'goal_type': args.goal_type,
            'audience': args.audience,
            'rigor': args.rigor,
            'granularity': args.granularity,
            'domain': args.domain,
        }
    )


def _parse_json_object(raw: str, *, field_name: str) -> dict:
    text = str(raw or '').strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('Invalid JSON for %s: %s' % (field_name, exc)) from exc
    if not isinstance(payload, dict):
        raise ValueError('%s must be a JSON object.' % field_name)
    return payload


def _parse_corpus_asset_spec(raw: str, *, index: int) -> dict:
    text = str(raw or '').strip()
    if not text:
        raise ValueError('Corpus asset spec cannot be empty.')
    if text.startswith('{'):
        payload = _parse_json_object(text, field_name='asset')
        payload.setdefault('role', 'primary' if index == 0 else 'supporting')
        return payload
    if '=' not in text:
        raise ValueError('Corpus asset spec must be "modality=source_uri" or JSON object string.')
    modality, source_uri = text.split('=', 1)
    modality_text = modality.strip()
    source_uri_text = source_uri.strip()
    if not modality_text or not source_uri_text:
        raise ValueError('Corpus asset spec must include both modality and source_uri.')
    return {
        'modality': modality_text,
        'source_uri': source_uri_text,
        'role': 'primary' if index == 0 else 'supporting',
    }


def _corpus_request_from_args(args: argparse.Namespace) -> CorpusDistillRequest:
    if args.payload_file:
        payload_text = Path(args.payload_file).read_text(encoding='utf-8')
        return CorpusDistillRequest.from_dict(_parse_json_object(payload_text, field_name='payload-file'))

    if args.payload_json:
        return CorpusDistillRequest.from_dict(_parse_json_object(args.payload_json, field_name='payload-json'))

    assets_payload = [
        _parse_corpus_asset_spec(spec, index=index)
        for index, spec in enumerate(args.asset)
    ]
    if not assets_payload:
        raise ValueError('distill-corpus requires at least one --asset or --payload-file/--payload-json.')

    metadata_payload = _parse_json_object(args.metadata_json, field_name='metadata-json') if args.metadata_json else {}
    request_payload = {
        'name': str(args.name or '').strip(),
        'assets': assets_payload,
        'goal': _goal_from_args(args).to_dict(),
        'tags': [str(item).strip() for item in (args.tags or []) if str(item).strip()],
        'metadata': metadata_payload,
    }
    return CorpusDistillRequest.from_dict(request_payload)


def _normalize_publication_type(raw: str) -> str:
    normalized = str(raw or '').strip().lower()
    if not normalized:
        return PublicationType.SKILL_MARKDOWN.value
    if normalized.startswith('publication_'):
        normalized = normalized[len('publication_') :]
    return normalized


def _supported_publication_types() -> list[str]:
    return [item.value for item in PublicationType]


def _normalize_export_target(raw: str) -> AgentSkillTarget:
    normalized = str(raw or '').strip().lower()
    if not normalized:
        return AgentSkillTarget.PORTABLE
    try:
        return AgentSkillTarget(normalized)
    except ValueError as exc:
        valid = ', '.join(item.value for item in AgentSkillTarget)
        raise ValueError('Unsupported export target: %s (valid: %s)' % (normalized, valid)) from exc


def _resolve_available_publications(bundle) -> list[str]:
    available: list[str] = []

    publications = getattr(bundle, 'publications', None)
    if isinstance(publications, list):
        for publication in publications:
            publication_type = getattr(publication, 'publication_type', None)
            value = getattr(publication_type, 'value', None)
            if value is None and isinstance(publication, dict):
                value = publication.get('publication_type')
            if value is None:
                continue
            normalized = _normalize_publication_type(str(value))
            if normalized and normalized not in available:
                available.append(normalized)

    adapter_metadata = getattr(bundle, 'adapter_metadata', {})
    if isinstance(adapter_metadata, dict):
        types_payload = adapter_metadata.get('publication_types', [])
        if isinstance(types_payload, list):
            for value in types_payload:
                normalized = _normalize_publication_type(str(value))
                if normalized and normalized not in available:
                    available.append(normalized)

    artifacts = getattr(bundle, 'artifacts', {})
    if isinstance(artifacts, dict):
        for key in artifacts:
            key_text = str(key or '').strip().lower()
            if not key_text.startswith('publication_'):
                continue
            normalized = _normalize_publication_type(key_text)
            if normalized and normalized not in available:
                available.append(normalized)

    return available


def _resolve_publication_path(bundle, publication_type: str) -> str:
    requested = _normalize_publication_type(publication_type)
    artifacts = getattr(bundle, 'artifacts', {})
    if not isinstance(artifacts, dict):
        return ''

    preferred_key = 'publication_%s' % requested
    preferred_path = str(artifacts.get(preferred_key, '')).strip()
    if preferred_path:
        return preferred_path

    fallback_keys = {
        PublicationType.SKILL_MARKDOWN.value: 'skill_markdown',
        PublicationType.SKILL_JSON.value: 'skill',
    }
    fallback_key = fallback_keys.get(requested, '')
    if fallback_key:
        fallback_path = str(artifacts.get(fallback_key, '')).strip()
        if fallback_path:
            return fallback_path

    return str(artifacts.get('skill_markdown', '')).strip()


def _resolve_review_task_payload(bundle) -> dict:
    review_task = getattr(bundle, 'review_task', None)
    if hasattr(review_task, 'to_dict'):
        payload = review_task.to_dict()
        if isinstance(payload, dict):
            return payload
    if isinstance(review_task, dict):
        return dict(review_task)

    adapter_metadata = getattr(bundle, 'adapter_metadata', {})
    if not isinstance(adapter_metadata, dict):
        return {}

    review_task_payload = adapter_metadata.get('review_task')
    if isinstance(review_task_payload, dict):
        return dict(review_task_payload)
    review_policy_payload = adapter_metadata.get('review_policy')
    if isinstance(review_policy_payload, dict):
        return {
            'decision': str(review_policy_payload.get('decision', '')).strip(),
            'status': str(review_policy_payload.get('status', '')).strip(),
            'reason_codes': review_policy_payload.get('reason_codes', []),
        }
    return {}


def _print_corpus_summary(bundle, *, requested_publication: str, show_publications: bool) -> None:
    available_publications = _resolve_available_publications(bundle)
    if show_publications:
        print('selected_publication=%s' % requested_publication)
        print('available_publications=%s' % ','.join(available_publications))

    review_payload = _resolve_review_task_payload(bundle)
    if review_payload:
        status = str(review_payload.get('status', '')).strip() or 'unknown'
        decision = str(review_payload.get('decision', '')).strip() or 'unknown'
        review_task_id = str(review_payload.get('review_task_id', '')).strip() or '-'
        reason_codes_payload = review_payload.get('reason_codes', [])
        reason_codes: list[str] = []
        if isinstance(reason_codes_payload, list):
            for item in reason_codes_payload:
                reason_code = str(item).strip()
                if reason_code and reason_code not in reason_codes:
                    reason_codes.append(reason_code)
        reason_codes_text = ','.join(reason_codes) if reason_codes else '-'
        print(
            'review_status=%s decision=%s review_task_id=%s reason_codes=%s'
            % (status, decision, review_task_id, reason_codes_text)
        )


def main(argv: list = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = build_service()

    if args.command == 'distill-text':
        bundle = service.distill_text(
            TextDistillRequest(
                title=args.title,
                content=args.content,
                file_path=args.file_path,
                goal=_goal_from_args(args),
            )
        )
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'distill-audio':
        bundle = service.distill_audio(
            AudioDistillRequest(
                title=args.title,
                audio_path=args.audio_path,
                transcript=args.transcript,
                transcript_path=args.transcript_path,
                language=args.language,
                prompt=args.prompt,
                goal=_goal_from_args(args),
            )
        )
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'distill-image':
        bundle = service.distill_image(
            ImageDistillRequest(
                image_path=args.image_path,
                title=args.title,
                goal=_goal_from_args(args),
            )
        )
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'distill-tabular':
        bundle = service.distill_tabular(
            TabularDistillRequest(
                file_path=args.file_path,
                title=args.title,
                time_column=args.time_column,
                value_columns=args.value_columns or [],
                entity_columns=args.entity_columns or [],
                max_series=args.max_series,
                goal=_goal_from_args(args),
            )
        )
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'distill-video':
        bundle = service.distill_video(
            VideoDistillRequest(
                video_path=args.video_path,
                title=args.title,
                transcript=args.transcript,
                transcript_path=args.transcript_path,
                language=args.language,
                prompt=args.prompt,
                keyframe_interval_seconds=args.keyframe_interval_seconds,
                max_keyframes=args.max_keyframes,
                scene_threshold=args.scene_threshold,
                dedupe_distance=args.dedupe_distance,
                goal=_goal_from_args(args),
            )
        )
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'distill-corpus':
        try:
            request = _corpus_request_from_args(args)
        except ValueError as exc:
            parser.error(str(exc))
        requested_publication = _normalize_publication_type(args.publication)
        if requested_publication not in _supported_publication_types():
            parser.error(
                'Unsupported publication type: %s (valid: %s)'
                % (requested_publication, ', '.join(_supported_publication_types()))
            )
        bundle = service.distill_corpus(request)
        print(_resolve_publication_path(bundle, requested_publication))
        _print_corpus_summary(
            bundle,
            requested_publication=requested_publication,
            show_publications=args.show_publications,
        )
        return 0

    if args.command == 'show-template':
        from omni_skill_pipeline.config import load_settings

        settings = load_settings()
        print(settings.template_path)
        print(settings.template_path.read_text(encoding='utf-8'))
        return 0

    if args.command == 'export-skill':
        try:
            export_target = _normalize_export_target(args.target)
        except ValueError as exc:
            parser.error(str(exc))
        exporter = AgentSkillExporter(output_root=Path(args.output_root))
        try:
            results = exporter.export_from_bundle(bundle_path=Path(args.bundle), target=export_target)
        except ValueError as exc:
            parser.error(str(exc))
        for result in results:
            print(
                'target=%s skill=%s package=%s'
                % (result.target.value, result.skill_path, result.package_path)
            )
        return 0

    if args.command == 'validate-skill':
        report = validate_skill_package(
            package_path=Path(args.package),
            max_lines=int(args.max_lines),
        )
        print('status=%s package=%s skill=%s' % (report.status, report.package_path, report.skill_path))
        if report.failure_codes:
            print('failure_codes=%s' % ','.join(report.failure_codes))
        for issue in report.issues:
            print('issue[%s]=%s' % (issue.code, issue.message))
        return 0 if report.status == 'pass' else 2

    parser.print_help(sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
