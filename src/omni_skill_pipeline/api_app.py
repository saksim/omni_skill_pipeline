from __future__ import annotations

from omni_skill_pipeline.models import (
    AudioDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import PlainTextResponse
except ImportError:  # pragma: no cover
    FastAPI = None
    HTTPException = Exception
    PlainTextResponse = object


def create_app():
    if FastAPI is None:
        raise RuntimeError('FastAPI is not installed. Install with `pip install .[api]`.')

    app = FastAPI(title='Omni Skill Pipeline', version='0.2.0')
    service = build_service()

    @app.get('/healthz')
    def healthz():
        return {'status': 'ok'}

    @app.get('/v1/templates/skill', response_class=PlainTextResponse)
    def get_template():
        from omni_skill_pipeline.config import load_settings

        settings = load_settings()
        return settings.template_path.read_text(encoding='utf-8')

    @app.post('/v1/distill/text')
    def distill_text(payload: dict):
        try:
            request = TextDistillRequest(
                title=payload.get('title'),
                content=payload.get('content'),
                file_path=payload.get('file_path'),
                goal=DistillGoal.from_dict(payload.get('goal')),
            )
            return service.distill_text(request).to_dict()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post('/v1/distill/audio')
    def distill_audio(payload: dict):
        try:
            request = AudioDistillRequest(
                title=payload.get('title'),
                audio_path=payload.get('audio_path'),
                transcript=payload.get('transcript'),
                transcript_path=payload.get('transcript_path'),
                language=payload.get('language'),
                prompt=payload.get('prompt'),
                goal=DistillGoal.from_dict(payload.get('goal')),
            )
            return service.distill_audio(request).to_dict()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post('/v1/distill/image')
    def distill_image(payload: dict):
        try:
            request = ImageDistillRequest(
                image_path=payload['image_path'],
                title=payload.get('title'),
                goal=DistillGoal.from_dict(payload.get('goal')),
            )
            return service.distill_image(request).to_dict()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post('/v1/distill/tabular')
    def distill_tabular(payload: dict):
        try:
            request = TabularDistillRequest(
                file_path=payload['file_path'],
                title=payload.get('title'),
                time_column=payload.get('time_column'),
                value_columns=[str(item) for item in payload.get('value_columns', [])],
                entity_columns=[str(item) for item in payload.get('entity_columns', [])],
                max_series=int(payload.get('max_series', 6)),
                goal=DistillGoal.from_dict(payload.get('goal')),
            )
            return service.distill_tabular(request).to_dict()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post('/v1/distill/video')
    def distill_video(payload: dict):
        try:
            request = VideoDistillRequest(
                video_path=payload['video_path'],
                title=payload.get('title'),
                transcript=payload.get('transcript'),
                transcript_path=payload.get('transcript_path'),
                language=payload.get('language'),
                prompt=payload.get('prompt'),
                keyframe_interval_seconds=payload.get('keyframe_interval_seconds'),
                max_keyframes=payload.get('max_keyframes'),
                scene_threshold=payload.get('scene_threshold'),
                dedupe_distance=payload.get('dedupe_distance'),
                goal=DistillGoal.from_dict(payload.get('goal')),
            )
            return service.distill_video(request).to_dict()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=400, detail=str(exc))

    return app


app = create_app() if FastAPI is not None else None
