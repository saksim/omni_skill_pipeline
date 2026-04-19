from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    draft_dir: Path
    published_dir: Path
    template_path: Path
    schema_path: Path
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    llm_model: str
    vision_model: str
    transcription_model: str
    transcription_language: Optional[str]
    ffmpeg_bin: str
    ffprobe_bin: str
    tesseract_bin: str
    tesseract_languages: str
    keyframe_interval_seconds: int
    max_keyframes: int
    video_scene_threshold: float
    video_frame_dedupe_distance: int
    prefer_llm_composer: bool


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(repo_root: Path = None) -> Settings:
    root = Path(repo_root) if repo_root else get_repo_root()
    return Settings(
        repo_root=root,
        draft_dir=root / 'skills' / 'drafts',
        published_dir=root / 'skills' / 'published',
        template_path=root / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
        schema_path=root / 'docs' / 'current' / 'contracts' / 'skill.schema.json',
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_base_url=os.getenv('OPENAI_BASE_URL'),
        llm_model=os.getenv('OMNI_OPENAI_LLM_MODEL', 'gpt-4.1'),
        vision_model=os.getenv('OMNI_OPENAI_VISION_MODEL', 'gpt-4.1-mini'),
        transcription_model=os.getenv('OMNI_OPENAI_TRANSCRIBE_MODEL', 'gpt-4o-transcribe'),
        transcription_language=os.getenv('OMNI_TRANSCRIPTION_LANGUAGE'),
        ffmpeg_bin=os.getenv('OMNI_FFMPEG_BIN', 'ffmpeg'),
        ffprobe_bin=os.getenv('OMNI_FFPROBE_BIN', 'ffprobe'),
        tesseract_bin=os.getenv('OMNI_TESSERACT_BIN', 'tesseract'),
        tesseract_languages=os.getenv('OMNI_TESSERACT_LANGUAGES', 'eng+chi_sim'),
        keyframe_interval_seconds=int(os.getenv('OMNI_KEYFRAME_INTERVAL_SECONDS', '8')),
        max_keyframes=int(os.getenv('OMNI_MAX_KEYFRAMES', '6')),
        video_scene_threshold=float(os.getenv('OMNI_VIDEO_SCENE_THRESHOLD', '0.32')),
        video_frame_dedupe_distance=int(os.getenv('OMNI_VIDEO_FRAME_DEDUPE_DISTANCE', '5')),
        prefer_llm_composer=_env_flag('OMNI_PREFER_LLM_COMPOSER', True),
    )
