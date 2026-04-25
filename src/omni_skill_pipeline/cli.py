from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from omni_skill_pipeline.models import (
    AudioDistillRequest,
    CorpusDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service


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
    _attach_goal_args(corpus_parser)

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
        bundle = service.distill_corpus(request)
        print(bundle.artifacts.get('skill_markdown', ''))
        return 0

    if args.command == 'show-template':
        from omni_skill_pipeline.config import load_settings

        settings = load_settings()
        print(settings.template_path)
        print(settings.template_path.read_text(encoding='utf-8'))
        return 0

    parser.print_help(sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
