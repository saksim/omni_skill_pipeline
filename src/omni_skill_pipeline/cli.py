from __future__ import annotations

import argparse
import sys

from omni_skill_pipeline.models import (
    AudioDistillRequest,
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
