from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from validate_manifest import validate_manifest  # noqa: E402

from omni_skill_pipeline.adapters.audio import AudioAdapter  # noqa: E402
from omni_skill_pipeline.adapters.image import ImageAdapter  # noqa: E402
from omni_skill_pipeline.adapters.tabular import TabularAdapter  # noqa: E402
from omni_skill_pipeline.adapters.text import TextAdapter  # noqa: E402
from omni_skill_pipeline.adapters.video import VideoAdapter  # noqa: E402
from omni_skill_pipeline.config import load_settings  # noqa: E402
from omni_skill_pipeline.exporters import AgentSkillExporter  # noqa: E402
from omni_skill_pipeline.models import (  # noqa: E402
    AgentSkillTarget,
    AudioDistillRequest,
    CorpusAssetInput,
    CorpusDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    Modality,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer  # noqa: E402
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult, SampledFrame, VideoMetadata  # noqa: E402
from omni_skill_pipeline.quality.review_policy import ReviewPolicy  # noqa: E402
from omni_skill_pipeline.quality.trial_metrics import (  # noqa: E402
    TrialMetricsCollector,
    render_trial_metrics_markdown_summary,
)
from omni_skill_pipeline.repository import FileArtifactRepository  # noqa: E402
from omni_skill_pipeline.service import DistillationService, build_service  # noqa: E402
from omni_skill_pipeline.validation import validate_skill_package  # noqa: E402
from omni_skill_pipeline.validation import evaluate_trial_security_from_bundle  # noqa: E402

DEFAULT_MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "trial-manifests"
    / "trial-sample-mixed-corpus.example.json"
)
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
)
DEFAULT_PLAN_PATH = "controlled-trial-execution-plan.json"
DEFAULT_RUN_REPORT_PATH = "controlled-trial-run-report.json"
DEFAULT_METRICS_MANIFEST_PATH = "trial-metrics-manifest.json"
DEFAULT_METRICS_REPORT_PATH = "trial-metrics-report.json"
DEFAULT_METRICS_SUMMARY_PATH = "trial-metrics-summary.md"

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
TABULAR_SUFFIXES = {".csv", ".tsv", ".xls", ".xlsx"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".log", ".pdf", ".doc", ".docx", ".json", ".html", ".htm", ".srt"}
SUPPORTED_EVIDENCE_ORIGINS = {"real", "fixture", "synthetic"}


class FixtureOCRProvider(object):
    def extract(self, image_path: Path) -> OCRResult:
        stem = image_path.stem.replace("-", " ")
        return OCRResult(
            text="Fixture OCR: %s\nstatus: degraded" % stem,
            blocks=[
                OCRBlock(text="Fixture OCR: %s" % stem, confidence=0.91),
                OCRBlock(text="status: degraded", confidence=0.89),
            ],
            engine="fixture-ocr",
        )


class FixtureImageAnalyzer(object):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        return FrameAnalysis(
            image_path=image_path,
            summary="Fixture scene summary for %s." % image_path.stem,
            tags=["fixture", "scene", image_path.suffix.lower().lstrip(".")],
        )


class FixtureMediaProcessor(object):
    def __init__(self, frame_source: Path) -> None:
        self.frame_source = Path(frame_source).resolve()

    def probe(self, video_path: Path) -> VideoMetadata:
        return VideoMetadata(duration_seconds=9.0, width=640, height=360, fps=1.0, frame_count=9)

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        output = work_dir / "fixture_audio.wav"
        output.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt ")
        output.with_suffix(".srt").write_text(
            "\n".join(
                [
                    "1",
                    "00:00:01,000 --> 00:00:03,000",
                    "Open release dashboard and verify GO gate.",
                    "",
                    "2",
                    "00:00:03,000 --> 00:00:05,000",
                    "Compare latency and error trends after rollout.",
                    "",
                    "3",
                    "00:00:05,000 --> 00:00:07,000",
                    "If regression persists, roll back and attach evidence.",
                ]
            ),
            encoding="utf-8",
        )
        return output

    def extract_keyframes(
        self,
        video_path: Path,
        work_dir: Path,
        *,
        interval_seconds: int,
        max_frames: int,
        scene_threshold: float | None = None,
        dedupe_distance: int | None = None,
    ) -> list[SampledFrame]:
        frames: list[SampledFrame] = []
        frame_count = min(max(1, int(max_frames)), 2)
        for index in range(1, frame_count + 1):
            frame_path = work_dir / ("frame_%03d.png" % index)
            frame_path.write_bytes(self.frame_source.read_bytes())
            frames.append(
                SampledFrame(
                    path=frame_path,
                    source="scene" if index == 1 else "timeline",
                    timestamp_seconds=float(index * 2),
                )
            )
        return frames


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one controlled-trial loop from a CBT-02 trial manifest: "
            "distill -> forced review mode -> reviewer packet -> simulated approval -> export -> "
            "skill validation -> trial metrics report."
        ),
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Trial manifest path (CBT-02 format).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for execution plan and run artifacts.",
    )
    parser.add_argument(
        "--sample-id",
        action="append",
        default=[],
        help="Optional sample_id filter. Repeat to run multiple samples.",
    )
    parser.add_argument(
        "--target",
        default="",
        help="Optional export target override (codex/claude-code/opencode/portable/all).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print/write execution plan only without running distillation.",
    )
    parser.add_argument(
        "--use-fixture-stubs",
        action="store_true",
        help="Use offline fixture providers (no external provider/ffmpeg dependency).",
    )
    parser.set_defaults(force_review_mode=True)
    parser.add_argument(
        "--disable-force-review-mode",
        dest="force_review_mode",
        action="store_false",
        help="Disable forced trial review mode env injection (not recommended for CBT loops).",
    )
    parser.add_argument(
        "--review-reason-code",
        default="controlled_trial_requires_review",
        help="Reason code persisted when forced review mode is enabled.",
    )
    parser.add_argument(
        "--release-decision",
        default="GO",
        choices=["GO", "HOLD"],
        help="Release decision value recorded in metrics manifest.",
    )
    parser.add_argument(
        "--simulated-reviewer-edit-distance-pct",
        type=float,
        default=20.0,
        help="Synthetic edit-distance percentage used for this loop metrics row.",
    )
    parser.add_argument(
        "--simulated-agent-smoke-result",
        default="not_run",
        choices=["passed", "failed", "not_run"],
        help="Synthetic agent smoke status for this loop metrics row.",
    )
    parser.add_argument(
        "--max-skill-lines",
        type=int,
        default=500,
        help="Max line budget passed into skill usability validation.",
    )
    parser.add_argument(
        "--fail-on-ga-blocker",
        action="store_true",
        help="Exit with code 1 when metrics report has critical GA blockers.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print run report JSON to stdout on completion.",
    )
    return parser.parse_args()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _resolve_manifest_uri(uri: str, *, repo_root: Path) -> Path:
    raw = str(uri or "").strip()
    if not raw:
        raise ValueError("Asset uri cannot be empty.")
    parsed = urlparse(raw)
    if parsed.scheme.lower() == "file":
        resolved = unquote(parsed.path or "")
        if parsed.netloc and resolved and not resolved.startswith("/"):
            resolved = "/%s/%s" % (parsed.netloc, resolved)
        if len(resolved) >= 3 and resolved[0] == "/" and resolved[2] == ":":
            resolved = resolved[1:]
        if not resolved:
            raise ValueError("Invalid file:// uri: %s" % raw)
        return Path(resolved).resolve()
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def _infer_modality(*, sample_modality: str, asset_type: str, asset_path: Path) -> str:
    normalized_sample = str(sample_modality).strip().lower()
    normalized_type = str(asset_type).strip().lower()
    suffix = asset_path.suffix.lower()
    if normalized_type in {"audio", "recording"} or suffix in AUDIO_SUFFIXES:
        return "audio"
    if normalized_type in {"image", "screenshot", "png", "jpeg", "jpg", "diagram"} or suffix in IMAGE_SUFFIXES:
        return "image"
    if normalized_type in {"video", "screen_recording"} or suffix in VIDEO_SUFFIXES:
        return "video"
    if normalized_type in {"table", "tabular", "csv", "tsv", "timeseries"} or suffix in TABULAR_SUFFIXES:
        return "tabular"
    if normalized_type in {"subtitle", "transcript", "document", "markdown", "pdf"} or suffix in TEXT_SUFFIXES:
        return "text"
    if normalized_sample == "mixed_corpus":
        return "text"
    if normalized_sample in {"text", "audio", "image", "video", "tabular"}:
        return normalized_sample
    return "text"


def _sample_assets_with_paths(sample: dict[str, Any], *, repo_root: Path) -> list[dict[str, Any]]:
    assets_raw = sample.get("asset_list", [])
    if not isinstance(assets_raw, list) or not assets_raw:
        raise ValueError("sample %s has empty asset_list." % str(sample.get("sample_id", "")).strip())
    rows: list[dict[str, Any]] = []
    for index, asset in enumerate(assets_raw):
        if not isinstance(asset, dict):
            raise ValueError("sample asset #%s must be an object." % (index + 1))
        uri = str(asset.get("uri", "")).strip()
        resolved = _resolve_manifest_uri(uri, repo_root=repo_root)
        if not resolved.exists():
            raise ValueError("Asset path does not exist: %s" % resolved)
        inferred_modality = _infer_modality(
            sample_modality=str(sample.get("modality", "")).strip().lower(),
            asset_type=str(asset.get("asset_type", "")).strip().lower(),
            asset_path=resolved,
        )
        rows.append(
            {
                "asset_id": str(asset.get("asset_id", "")).strip() or ("asset-%s" % (index + 1)),
                "asset_type": str(asset.get("asset_type", "")).strip(),
                "uri": uri,
                "resolved_path": str(resolved),
                "inferred_modality": inferred_modality,
            }
        )
    return rows


def _select_samples(manifest_payload: dict[str, Any], *, sample_ids: list[str]) -> list[dict[str, Any]]:
    samples_raw = manifest_payload.get("samples", [])
    if not isinstance(samples_raw, list) or not samples_raw:
        raise ValueError("Manifest requires non-empty samples list.")
    selected = []
    sample_id_filter = {str(item).strip() for item in sample_ids if str(item).strip()}
    for item in samples_raw:
        if not isinstance(item, dict):
            continue
        sample_id = str(item.get("sample_id", "")).strip()
        if sample_id_filter and sample_id not in sample_id_filter:
            continue
        selected.append(item)
    if not selected:
        raise ValueError("No samples selected from manifest.")
    return selected


def _to_modality_enum(name: str) -> Modality:
    normalized = str(name).strip().lower()
    if normalized == "mixed_corpus":
        return Modality.TEXT
    return Modality(normalized)


def _build_goal() -> DistillGoal:
    return DistillGoal.from_dict(
        {
            "goal_type": "build_skill",
            "audience": "self",
            "rigor": "draft",
            "granularity": "task",
            "domain": "controlled_trial",
        }
    )


def _pick_first_asset_by_modality(assets: list[dict[str, Any]], modality: str) -> dict[str, Any]:
    for asset in assets:
        if str(asset.get("inferred_modality", "")).strip().lower() == modality:
            return asset
    return assets[0]


def _pick_transcript_asset(assets: list[dict[str, Any]], primary_path: str) -> str:
    primary_resolved = Path(primary_path).resolve()
    for asset in assets:
        candidate = Path(str(asset.get("resolved_path", "")).strip()).resolve()
        if candidate == primary_resolved:
            continue
        suffix = candidate.suffix.lower()
        if suffix in {".srt", ".txt", ".md", ".json"}:
            return str(candidate)
    return ""


def _request_for_sample(sample: dict[str, Any], assets: list[dict[str, Any]]) -> tuple[str, object]:
    modality = str(sample.get("modality", "")).strip().lower()
    goal = _build_goal()
    title = str(sample.get("scenario", "")).strip() or str(sample.get("sample_id", "")).strip()
    if modality == "text":
        asset = _pick_first_asset_by_modality(assets, "text")
        return "text", TextDistillRequest(title=title, file_path=str(asset["resolved_path"]), goal=goal)
    if modality == "audio":
        primary = _pick_first_asset_by_modality(assets, "audio")
        transcript_path = _pick_transcript_asset(assets, str(primary["resolved_path"]))
        return (
            "audio",
            AudioDistillRequest(
                title=title,
                audio_path=str(primary["resolved_path"]),
                transcript_path=transcript_path or None,
                goal=goal,
            ),
        )
    if modality == "image":
        primary = _pick_first_asset_by_modality(assets, "image")
        return "image", ImageDistillRequest(image_path=str(primary["resolved_path"]), title=title, goal=goal)
    if modality == "video":
        primary = _pick_first_asset_by_modality(assets, "video")
        transcript_path = _pick_transcript_asset(assets, str(primary["resolved_path"]))
        return (
            "video",
            VideoDistillRequest(
                video_path=str(primary["resolved_path"]),
                transcript_path=transcript_path or None,
                title=title,
                goal=goal,
            ),
        )
    if modality == "tabular":
        primary = _pick_first_asset_by_modality(assets, "tabular")
        return (
            "tabular",
            TabularDistillRequest(
                file_path=str(primary["resolved_path"]),
                title=title,
                goal=goal,
            ),
        )
    if modality == "mixed_corpus":
        corpus_assets: list[CorpusAssetInput] = []
        for index, asset in enumerate(assets):
            inferred = str(asset.get("inferred_modality", "text")).strip().lower()
            corpus_assets.append(
                CorpusAssetInput(
                    source_uri=str(asset["resolved_path"]),
                    modality=_to_modality_enum(inferred),
                    role="primary" if index == 0 else "supporting",
                    title_hint=str(asset.get("asset_type", "")).strip() or str(asset.get("asset_id", "")).strip(),
                )
            )
        return (
            "mixed_corpus",
            CorpusDistillRequest(
                name=title or "controlled trial mixed corpus",
                assets=corpus_assets,
                goal=goal,
                tags=["controlled_trial", "fixture_manifest"],
                metadata={"sample_id": str(sample.get("sample_id", "")).strip()},
            ),
        )
    raise ValueError("Unsupported sample modality: %s" % modality)


def _normalize_target(raw: str) -> AgentSkillTarget:
    text = str(raw or "").strip().lower()
    if not text:
        return AgentSkillTarget.PORTABLE
    try:
        return AgentSkillTarget(text)
    except ValueError as exc:
        valid = ", ".join(item.value for item in AgentSkillTarget)
        raise ValueError("Unsupported export target: %s (valid: %s)" % (text, valid)) from exc


def _normalize_evidence_origin(raw: Any) -> str:
    normalized = str(raw if raw is not None else "fixture").strip().lower() or "fixture"
    if normalized not in SUPPORTED_EVIDENCE_ORIGINS:
        raise ValueError(
            "Unsupported evidence_origin: %s (valid: %s)"
            % (normalized, ", ".join(sorted(SUPPORTED_EVIDENCE_ORIGINS)))
        )
    return normalized


def _build_execution_plan(
    *,
    manifest_path: Path,
    manifest_payload: dict[str, Any],
    samples: list[dict[str, Any]],
    repo_root: Path,
    target_override: str,
    use_fixture_stubs: bool,
    force_review_mode: bool,
    review_reason_code: str,
) -> dict[str, Any]:
    sample_plans: list[dict[str, Any]] = []
    for sample in samples:
        sample_id = str(sample.get("sample_id", "")).strip()
        assets = _sample_assets_with_paths(sample, repo_root=repo_root)
        modality, _ = _request_for_sample(sample, assets)
        target = target_override or str(sample.get("target_package_format", "")).strip() or "portable"
        sample_plans.append(
            {
                "sample_id": sample_id,
                "modality": modality,
                "target": target,
                "assets": assets,
                "steps": [
                    "distill_input",
                    "assert_review_packet",
                    "simulate_human_approval",
                    "export_skill_package",
                    "validate_skill_package",
                    "append_trial_metrics_loop",
                ],
            }
        )
    return {
        "generated_at_utc": _utc_now_iso(),
        "manifest_path": str(manifest_path),
        "manifest_id": str(manifest_payload.get("manifest_id", "")).strip(),
        "sample_count": len(sample_plans),
        "use_fixture_stubs": bool(use_fixture_stubs),
        "force_review_mode": bool(force_review_mode),
        "review_reason_code": review_reason_code,
        "samples": sample_plans,
    }


def _set_forced_review_mode(force_review_mode: bool, review_reason_code: str) -> None:
    if not force_review_mode:
        return
    os.environ["OMNI_CONTROLLED_TRIAL_REVIEW_MODE"] = "1"
    os.environ["OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE"] = str(review_reason_code).strip() or "controlled_trial_requires_review"


def _build_fixture_service() -> DistillationService:
    settings = load_settings(REPO_ROOT)
    repository = FileArtifactRepository(settings.draft_dir)
    ocr_provider = FixtureOCRProvider()
    analyzer = FixtureImageAnalyzer()
    audio_adapter = AudioAdapter()

    frame_source = settings.repo_root / "examples" / "trial" / "image" / "service-latency-dashboard.png"
    if not frame_source.is_file():
        raise ValueError("Fixture frame source missing: %s" % frame_source)
    video_adapter = VideoAdapter(
        media_processor=FixtureMediaProcessor(frame_source=frame_source),
        audio_adapter=audio_adapter,
        ocr_provider=ocr_provider,
        analyzer=analyzer,
        default_interval_seconds=3,
        default_max_keyframes=2,
        scratch_root=settings.repo_root / ".tmp_omni_media",
    )
    return DistillationService(
        repository=repository,
        text_adapter=TextAdapter(),
        audio_adapter=audio_adapter,
        image_adapter=ImageAdapter(ocr_provider=ocr_provider, analyzer=analyzer),
        tabular_adapter=TabularAdapter(),
        video_adapter=video_adapter,
        insight_extractor=HeuristicInsightExtractor(),
        skill_composer=HeuristicSkillComposer(),
        review_policy=ReviewPolicy(
            force_review_mode=True,
            force_review_reason_code=str(os.getenv("OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE", "controlled_trial_requires_review")).strip(),
        ),
    )


def _simulate_human_approval(*, bundle_path: Path, output_path: Path) -> None:
    payload = _read_json(bundle_path)
    skill_payload = payload.get("skill")
    if isinstance(skill_payload, dict):
        skill_payload["review_status"] = "published"
    review_task_payload = payload.get("review_task")
    if isinstance(review_task_payload, dict):
        review_task_payload["status"] = "published"
        review_task_payload["decision"] = "auto_publish"
        reason_codes = review_task_payload.get("reason_codes", [])
        if isinstance(reason_codes, list) and "simulated_human_approval" not in reason_codes:
            reason_codes.append("simulated_human_approval")
        review_task_payload["review_notes"] = "Simulated human approval in controlled-trial runner."

    payload["simulated_review"] = {
        "approved_at_utc": _utc_now_iso(),
        "approved_by": "controlled-trial-runner",
        "mode": "simulated",
    }
    _write_json(output_path, payload)


def _provider_summary(bundle) -> dict[str, int]:
    provider_footprint = bundle.adapter_metadata.get("provider_footprint", {}) if isinstance(bundle.adapter_metadata, dict) else {}
    summary = provider_footprint.get("summary", {}) if isinstance(provider_footprint, dict) else {}
    if not isinstance(summary, dict):
        return {"calls": 0, "failures": 0}
    return {
        "calls": max(0, int(summary.get("total_calls", 0) or 0)),
        "failures": max(0, int(summary.get("total_failures", 0) or 0)),
    }


def _run_sample(
    *,
    sample: dict[str, Any],
    assets: list[dict[str, Any]],
    service: DistillationService,
    output_dir: Path,
    target_override: str,
    max_skill_lines: int,
    simulated_reviewer_edit_distance_pct: float,
    simulated_agent_smoke_result: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    sample_id = str(sample.get("sample_id", "")).strip() or "sample"
    target_raw = target_override or str(sample.get("target_package_format", "")).strip() or "portable"
    target = _normalize_target(target_raw)
    started = time.perf_counter()

    modality, request = _request_for_sample(sample, assets)
    if modality == "text":
        bundle = service.distill_text(request)
    elif modality == "audio":
        bundle = service.distill_audio(request)
    elif modality == "image":
        bundle = service.distill_image(request)
    elif modality == "video":
        bundle = service.distill_video(request)
    elif modality == "tabular":
        bundle = service.distill_tabular(request)
    elif modality == "mixed_corpus":
        bundle = service.distill_corpus(request)
    else:
        raise ValueError("Unsupported run modality: %s" % modality)
    latency_ms = round((time.perf_counter() - started) * 1000.0, 3)

    artifacts = bundle.artifacts if isinstance(bundle.artifacts, dict) else {}
    bundle_path_text = str(artifacts.get("bundle", "")).strip()
    if not bundle_path_text:
        raise ValueError("Sample %s missing bundle artifact path." % sample_id)
    bundle_path = Path(bundle_path_text).resolve()
    if not bundle_path.is_file():
        raise ValueError("Sample %s bundle file not found: %s" % (sample_id, bundle_path))

    reviewer_packet_path_text = str(artifacts.get("reviewer_packet", "")).strip()
    if not reviewer_packet_path_text:
        raise ValueError("Sample %s missing reviewer_packet artifact." % sample_id)
    reviewer_packet_path = Path(reviewer_packet_path_text).resolve()
    if not reviewer_packet_path.is_file():
        raise ValueError("Sample %s reviewer_packet missing: %s" % (sample_id, reviewer_packet_path))

    simulated_dir = output_dir / "simulated-approval"
    approved_bundle_path = simulated_dir / ("%s-bundle.approved.json" % sample_id)
    _simulate_human_approval(bundle_path=bundle_path, output_path=approved_bundle_path)
    trial_security_report = evaluate_trial_security_from_bundle(bundle_path=approved_bundle_path)
    if trial_security_report.status != "pass":
        raise ValueError(
            "Trial security gate failed for sample %s: %s"
            % (sample_id, ",".join(trial_security_report.failure_codes))
        )

    export_root = output_dir / "exports" / sample_id
    exporter = AgentSkillExporter(output_root=export_root)
    export_results = exporter.export_from_bundle(bundle_path=approved_bundle_path, target=target)
    validator_reports: list[dict[str, Any]] = []
    critical_leak = False
    for item in export_results:
        package_dir = item.package_path.parent
        report = validate_skill_package(package_path=package_dir, max_lines=max_skill_lines)
        report_payload = report.to_dict()
        report_payload["target"] = item.target.value
        report_payload["package_path"] = str(item.package_path)
        report_payload["skill_path"] = str(item.skill_path)
        validator_reports.append(report_payload)
        if report.status != "pass":
            raise ValueError(
                "Skill usability validation failed for sample %s target %s: %s"
                % (sample_id, item.target.value, ",".join(report.failure_codes))
            )
        if any(code in report.failure_codes for code in ("SECRET_TOKEN_LEAK", "ABSOLUTE_PATH_LEAK", "DANGEROUS_COMMAND_MARKER")):
            critical_leak = True

    provider = _provider_summary(bundle)
    evidence_origin = _normalize_evidence_origin(sample.get("evidence_origin", "fixture"))
    launch_gate_eligible_raw = sample.get("launch_gate_eligible", None)
    if launch_gate_eligible_raw is None:
        launch_gate_eligible = evidence_origin == "real"
    elif isinstance(launch_gate_eligible_raw, bool):
        launch_gate_eligible = launch_gate_eligible_raw
    elif isinstance(launch_gate_eligible_raw, str):
        launch_gate_eligible = launch_gate_eligible_raw.strip().lower() in {"1", "true", "yes", "y", "on"}
    else:
        launch_gate_eligible = bool(launch_gate_eligible_raw)
    launch_gate_ineligible_reason = str(sample.get("launch_gate_ineligible_reason", "")).strip()
    if not launch_gate_eligible and not launch_gate_ineligible_reason:
        if evidence_origin == "fixture":
            launch_gate_ineligible_reason = "fixture_evidence_not_launch_gate_eligible"
        elif evidence_origin == "synthetic":
            launch_gate_ineligible_reason = "synthetic_evidence_not_launch_gate_eligible"
        else:
            launch_gate_ineligible_reason = "explicitly_marked_not_launch_gate_eligible"
    source_system = str(sample.get("source_system", "")).strip()
    source_reference = str(sample.get("source_reference", "")).strip()
    collected_at_utc = str(sample.get("collected_at_utc", "")).strip()
    if evidence_origin == "real":
        if not source_system:
            source_system = "controlled_trial_runner"
        if not source_reference:
            source_reference = "sample://%s" % sample_id
        if not collected_at_utc:
            collected_at_utc = _utc_now_iso()
    review_task_payload = bundle.review_task
    review_task_id = ""
    if isinstance(review_task_payload, dict):
        review_task_id = str(review_task_payload.get("review_task_id", "")).strip()
    elif review_task_payload is not None:
        review_task_id = str(getattr(review_task_payload, "review_task_id", "")).strip()
    loop_row = {
        "loop_id": sample_id,
        "status": "complete",
        "modality": modality,
        "evidence_origin": evidence_origin,
        "launch_gate_eligible": launch_gate_eligible,
        "launch_gate_ineligible_reason": launch_gate_ineligible_reason,
        "review_outcome": "approved",
        "revisions_before_approval": 1,
        "reviewer_edit_distance_pct": float(simulated_reviewer_edit_distance_pct),
        "agent_smoke_result": simulated_agent_smoke_result,
        "published_without_review": False,
        "critical_secret_or_pii_leak": critical_leak,
        "high_severity_incident": False,
        "latency_ms": latency_ms,
        "provider_failure_count": int(provider["failures"]),
        "provider_call_count": int(provider["calls"]),
        "retry_count": 0,
        "artifact_count": len(artifacts),
        "estimated_cost_usd": 0.0,
        "review_task_id": review_task_id,
        "reviewed_by": "controlled-trial-runner",
        "reviewed_at_utc": _utc_now_iso(),
    }
    if evidence_origin == "real":
        loop_row["source_system"] = source_system
        loop_row["source_reference"] = source_reference
        loop_row["collected_at_utc"] = collected_at_utc
    sample_result = {
        "sample_id": sample_id,
        "modality": modality,
        "target": target.value,
        "bundle_path": str(bundle_path),
        "reviewer_packet_path": str(reviewer_packet_path),
        "approved_bundle_path": str(approved_bundle_path),
        "export_results": [
            {
                "target": item.target.value,
                "skill_path": str(item.skill_path),
                "package_path": str(item.package_path),
            }
            for item in export_results
        ],
        "validator_reports": validator_reports,
        "trial_security_gate_report": trial_security_report.to_dict(),
        "loop_metrics": loop_row,
    }
    return sample_result, loop_row


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        manifest_payload = _read_json(manifest_path)
        manifest_errors = validate_manifest(manifest_payload)
        if manifest_errors:
            raise ValueError("Manifest validation failed: %s" % "; ".join(manifest_errors))

        samples = _select_samples(manifest_payload, sample_ids=list(args.sample_id))
        plan = _build_execution_plan(
            manifest_path=manifest_path,
            manifest_payload=manifest_payload,
            samples=samples,
            repo_root=REPO_ROOT,
            target_override=str(args.target or "").strip(),
            use_fixture_stubs=bool(args.use_fixture_stubs),
            force_review_mode=bool(args.force_review_mode),
            review_reason_code=str(args.review_reason_code).strip(),
        )
        plan_path = output_dir / DEFAULT_PLAN_PATH
        _write_json(plan_path, plan)

        if args.dry_run:
            print("Controlled trial dry-run plan written: %s (samples=%s)" % (plan_path, plan.get("sample_count", 0)))
            if args.print_json:
                print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0

        _set_forced_review_mode(bool(args.force_review_mode), str(args.review_reason_code))
        service = _build_fixture_service() if bool(args.use_fixture_stubs) else build_service(repo_root=str(REPO_ROOT))

        sample_results: list[dict[str, Any]] = []
        loop_rows: list[dict[str, Any]] = []
        for sample in samples:
            sample_assets = _sample_assets_with_paths(sample, repo_root=REPO_ROOT)
            sample_result, loop_row = _run_sample(
                sample=sample,
                assets=sample_assets,
                service=service,
                output_dir=output_dir,
                target_override=str(args.target or "").strip(),
                max_skill_lines=max(1, int(args.max_skill_lines)),
                simulated_reviewer_edit_distance_pct=max(0.0, float(args.simulated_reviewer_edit_distance_pct)),
                simulated_agent_smoke_result=str(args.simulated_agent_smoke_result).strip().lower(),
            )
            sample_results.append(sample_result)
            loop_rows.append(loop_row)

        metrics_manifest = {
            "manifest_id": "cbt11-controlled-trial-loop",
            "manifest_version": "1.0",
            "generated_at_utc": _utc_now_iso(),
            "release_gate": {
                "latest_release_decision": str(args.release_decision).strip().upper(),
                "evidence_ref": "docs/working/status/baselines/e13-release-switch-decision-report.json",
            },
            "operator_signoff": {
                "cost_per_accepted_skill_accepted": True,
                "notes": "Simulated approval loop for controlled-trial runner.",
            },
            "loops": loop_rows,
        }
        metrics_manifest_path = output_dir / DEFAULT_METRICS_MANIFEST_PATH
        _write_json(metrics_manifest_path, metrics_manifest)

        collector = TrialMetricsCollector()
        metrics_report = collector.collect(metrics_manifest)
        metrics_summary = render_trial_metrics_markdown_summary(metrics_report)
        metrics_report_path = output_dir / DEFAULT_METRICS_REPORT_PATH
        metrics_summary_path = output_dir / DEFAULT_METRICS_SUMMARY_PATH
        _write_json(metrics_report_path, metrics_report)
        _write_text(metrics_summary_path, metrics_summary)

        run_report = {
            "run_id": "controlled-trial-%s" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "generated_at_utc": _utc_now_iso(),
            "manifest_path": str(manifest_path),
            "plan_path": str(plan_path),
            "sample_count": len(sample_results),
            "use_fixture_stubs": bool(args.use_fixture_stubs),
            "force_review_mode": bool(args.force_review_mode),
            "review_reason_code": str(args.review_reason_code).strip(),
            "samples": sample_results,
            "metrics_manifest_path": str(metrics_manifest_path),
            "metrics_report_path": str(metrics_report_path),
            "metrics_summary_path": str(metrics_summary_path),
            "metrics_status": str(metrics_report.get("overall_status", "unknown")),
            "ga_discussion_blocked": bool(metrics_report.get("ga_discussion_blocked")),
        }
        run_report_path = output_dir / DEFAULT_RUN_REPORT_PATH
        _write_json(run_report_path, run_report)

        print(
            "Controlled trial loop complete. samples=%s metrics_status=%s blockers=%s report=%s"
            % (
                len(sample_results),
                run_report["metrics_status"],
                "yes" if run_report["ga_discussion_blocked"] else "no",
                run_report_path,
            )
        )
        if args.print_json:
            print(json.dumps(run_report, ensure_ascii=False, indent=2))
        if bool(args.fail_on_ga_blocker) and bool(metrics_report.get("ga_discussion_blocked")):
            return 1
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Controlled trial run failed: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
