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
    api_key: Optional[str]
    rate_limit_requests: int
    rate_limit_window_seconds: int
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    openai_timeout_seconds: float
    openai_retry_max_attempts: int
    openai_retry_base_delay_seconds: float
    openai_circuit_breaker_consecutive_failures: int
    openai_circuit_breaker_cooldown_seconds: float
    openai_failure_budget_max_failures: int
    openai_failure_budget_window_seconds: float
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
    controlled_trial_review_mode: bool
    controlled_trial_review_reason_code: str
    portable_skill_markdown_line_limit: int
    artifact_repository_mode: str
    artifact_encryption_mode: str
    artifact_encryption_key: Optional[str]
    artifact_encryption_key_id: str
    postgres_repository_dsn: Optional[str]
    dual_write_continue_on_secondary_error: bool
    dual_write_secondary_prefix: str
    tenant_access_json: str
    tenant_access_file: str
    governance_ledger_dir: Path


def get_repo_root() -> Path:
    env_root = os.getenv('OMNI_REPO_ROOT')
    if env_root:
        return Path(env_root).resolve()

    current_workdir = Path.cwd().resolve()
    if (current_workdir / 'docs' / 'latest' / 'contracts' / 'SKILL.template.md').is_file():
        return current_workdir

    package_root = Path(__file__).resolve().parents[2]
    if (package_root / 'docs' / 'latest' / 'contracts' / 'SKILL.template.md').is_file():
        return package_root

    container_root = Path('/app')
    if (container_root / 'docs' / 'latest' / 'contracts' / 'SKILL.template.md').is_file():
        return container_root

    return package_root


def _packaged_contract_path(filename: str) -> Path:
    return Path(__file__).resolve().parent / 'resources' / 'contracts' / filename


def _resolve_contract_path(root: Path, filename: str) -> Path:
    repo_contract_path = root / 'docs' / 'latest' / 'contracts' / filename
    if repo_contract_path.is_file():
        return repo_contract_path
    packaged_contract_path = _packaged_contract_path(filename)
    if packaged_contract_path.is_file():
        return packaged_contract_path
    return repo_contract_path


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(repo_root: Path = None) -> Settings:
    root = Path(repo_root) if repo_root else get_repo_root()
    governance_ledger_raw = str(os.getenv('OMNI_GOVERNANCE_LEDGER_DIR', '')).strip()
    if governance_ledger_raw:
        governance_ledger_dir = Path(governance_ledger_raw)
        if not governance_ledger_dir.is_absolute():
            governance_ledger_dir = root / governance_ledger_dir
    else:
        governance_ledger_dir = root / 'skills' / 'drafts' / 'governance'
    return Settings(
        repo_root=root,
        draft_dir=root / 'skills' / 'drafts',
        published_dir=root / 'skills' / 'published',
        template_path=_resolve_contract_path(root, 'SKILL.template.md'),
        schema_path=_resolve_contract_path(root, 'skill.schema.json'),
        api_key=os.getenv('OMNI_API_KEY'),
        rate_limit_requests=int(os.getenv('OMNI_RATE_LIMIT_REQUESTS', '0')),
        rate_limit_window_seconds=int(os.getenv('OMNI_RATE_LIMIT_WINDOW_SECONDS', '60')),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_base_url=os.getenv('OPENAI_BASE_URL'),
        openai_timeout_seconds=float(os.getenv('OMNI_OPENAI_TIMEOUT_SECONDS', '60')),
        openai_retry_max_attempts=int(os.getenv('OMNI_OPENAI_RETRY_MAX_ATTEMPTS', '3')),
        openai_retry_base_delay_seconds=float(os.getenv('OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS', '0.5')),
        openai_circuit_breaker_consecutive_failures=int(
            os.getenv('OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES', '3')
        ),
        openai_circuit_breaker_cooldown_seconds=float(
            os.getenv('OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS', '30')
        ),
        openai_failure_budget_max_failures=int(os.getenv('OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES', '6')),
        openai_failure_budget_window_seconds=float(os.getenv('OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS', '60')),
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
        controlled_trial_review_mode=_env_flag('OMNI_CONTROLLED_TRIAL_REVIEW_MODE', False),
        controlled_trial_review_reason_code=(
            str(os.getenv('OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE', 'controlled_trial_requires_review')).strip()
            or 'controlled_trial_requires_review'
        ),
        portable_skill_markdown_line_limit=max(
            int(os.getenv('OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT', '220')),
            21,
        ),
        artifact_repository_mode=(
            str(os.getenv('OMNI_ARTIFACT_REPOSITORY_MODE', 'file')).strip() or 'file'
        ),
        artifact_encryption_mode=(
            str(os.getenv('OMNI_ARTIFACT_ENCRYPTION_MODE', '')).strip().lower()
        ),
        artifact_encryption_key=(
            str(os.getenv('OMNI_ARTIFACT_ENCRYPTION_KEY', '')).strip() or None
        ),
        artifact_encryption_key_id=(
            str(os.getenv('OMNI_ARTIFACT_ENCRYPTION_KEY_ID', 'default')).strip()
            or 'default'
        ),
        postgres_repository_dsn=(
            str(os.getenv('OMNI_POSTGRES_REPOSITORY_DSN', '')).strip() or None
        ),
        dual_write_continue_on_secondary_error=_env_flag(
            'OMNI_DUAL_WRITE_CONTINUE_ON_SECONDARY_ERROR',
            True,
        ),
        dual_write_secondary_prefix=(
            str(os.getenv('OMNI_DUAL_WRITE_SECONDARY_PREFIX', 'secondary_')).strip()
            or 'secondary_'
        ),
        tenant_access_json=str(os.getenv('OMNI_TENANT_ACCESS_JSON', '')).strip(),
        tenant_access_file=str(os.getenv('OMNI_TENANT_ACCESS_FILE', '')).strip(),
        governance_ledger_dir=governance_ledger_dir.resolve(),
    )
