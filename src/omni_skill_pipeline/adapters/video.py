from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.exceptions import MediaProcessingError, ProviderUnavailableError
from omni_skill_pipeline.extraction.modality.video_parser import VideoStructureParser
from omni_skill_pipeline.interfaces import ImageAnalyzer, MediaProcessor, OCRProvider
from omni_skill_pipeline.models import (
    Asset,
    AudioDistillRequest,
    ContentType,
    EvidenceUnit,
    LoadedAsset,
    Modality,
    VideoDistillRequest,
)
from omni_skill_pipeline.providers.base import SampledFrame
from omni_skill_pipeline.utils import unique_preserve_order


class VideoAdapter(object):
    def __init__(
        self,
        media_processor: MediaProcessor,
        audio_adapter: AudioAdapter,
        ocr_provider: OCRProvider | None = None,
        analyzer: ImageAnalyzer | None = None,
        *,
        default_interval_seconds: int = 8,
        default_max_keyframes: int = 6,
        default_scene_threshold: float = 0.32,
        default_dedupe_distance: int = 5,
        scratch_root: Path | None = None,
        video_parser: VideoStructureParser | None = None,
    ) -> None:
        self.media_processor = media_processor
        self.audio_adapter = audio_adapter
        self.ocr_provider = ocr_provider
        self.analyzer = analyzer
        self.video_parser = video_parser or VideoStructureParser()
        self.default_interval_seconds = default_interval_seconds
        self.default_max_keyframes = default_max_keyframes
        self.default_scene_threshold = default_scene_threshold
        self.default_dedupe_distance = default_dedupe_distance
        self.scratch_root = scratch_root or (Path.cwd() / '.tmp_omni_media')
        self.scratch_root.mkdir(parents=True, exist_ok=True)

    def load(self, request: VideoDistillRequest) -> LoadedAsset:
        request.validate()
        video_path = Path(request.video_path)
        if not video_path.exists():
            raise FileNotFoundError(str(video_path))

        video_metadata = self.media_processor.probe(video_path)
        asset = Asset(
            modality=Modality.VIDEO,
            source_uri=str(video_path.resolve()),
            metadata={
                'filename': video_path.name,
                'duration_seconds': video_metadata.duration_seconds,
                'width': video_metadata.width,
                'height': video_metadata.height,
                'fps': video_metadata.fps,
                'frame_count': video_metadata.frame_count,
            },
        )
        title_hint = request.title or video_path.stem.replace('_', ' ')
        evidence_units: list[EvidenceUnit] = []
        adapter_metadata = {
            'video_path': str(video_path.resolve()),
            'duration_seconds': video_metadata.duration_seconds,
            'fps': video_metadata.fps,
        }

        work_dir = self.scratch_root / ('omni_video_%s' % uuid4().hex)
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._collect_audio_evidence(asset, request, video_path, work_dir, evidence_units, adapter_metadata)
            sampled_frames = self._collect_frame_evidence(asset, request, video_path, work_dir, evidence_units, adapter_metadata)
            self._collect_timeline_evidence(asset, evidence_units, sampled_frames, adapter_metadata)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

        if not evidence_units:
            raise ValueError('Video adapter produced no evidence units.')

        return LoadedAsset(
            asset=asset,
            evidence_units=evidence_units,
            title_hint=title_hint,
            adapter_metadata=adapter_metadata,
        )

    def _collect_audio_evidence(
        self,
        asset: Asset,
        request: VideoDistillRequest,
        video_path: Path,
        work_dir: Path,
        evidence_units: list[EvidenceUnit],
        adapter_metadata: dict[str, object],
    ) -> None:
        try:
            audio_path = self.media_processor.extract_audio(video_path, work_dir)
        except (MediaProcessingError, ProviderUnavailableError):
            return

        try:
            loaded_audio = self.audio_adapter.load(
                AudioDistillRequest(
                    title=request.title,
                    audio_path=str(audio_path),
                    transcript=request.transcript,
                    transcript_path=request.transcript_path,
                    language=request.language,
                    prompt=request.prompt,
                    goal=request.goal,
                )
            )
        except Exception:
            return

        adapter_metadata['audio_track_extracted'] = True
        adapter_metadata['audio_evidence_count'] = len(loaded_audio.evidence_units)
        for unit in loaded_audio.evidence_units:
            evidence_units.append(
                EvidenceUnit(
                    asset_id=asset.asset_id,
                    span_ref='video:%s' % unit.span_ref,
                    content_type=ContentType.SPEECH,
                    content=unit.content,
                    speaker=unit.speaker,
                    confidence=unit.confidence,
                    tags=unique_preserve_order(unit.tags + ['source:audio_track']),
                )
            )

    def _collect_frame_evidence(
        self,
        asset: Asset,
        request: VideoDistillRequest,
        video_path: Path,
        work_dir: Path,
        evidence_units: list[EvidenceUnit],
        adapter_metadata: dict[str, object],
    ) -> list[SampledFrame]:
        interval_seconds = request.keyframe_interval_seconds or self.default_interval_seconds
        max_keyframes = request.max_keyframes or self.default_max_keyframes
        scene_threshold = request.scene_threshold if request.scene_threshold is not None else self.default_scene_threshold
        dedupe_distance = request.dedupe_distance if request.dedupe_distance is not None else self.default_dedupe_distance
        frames = self.media_processor.extract_keyframes(
            video_path,
            work_dir,
            interval_seconds=interval_seconds,
            max_frames=max_keyframes,
            scene_threshold=scene_threshold,
            dedupe_distance=dedupe_distance,
        )
        adapter_metadata['keyframes'] = [
            {
                'source': frame.source,
                'timestamp_seconds': frame.timestamp_seconds,
                'scene_score': frame.scene_score,
            }
            for frame in frames
        ]
        adapter_metadata['scene_threshold'] = scene_threshold
        adapter_metadata['dedupe_distance'] = dedupe_distance

        for index, frame in enumerate(frames, start=1):
            span_base = self._build_frame_span(index, frame)
            if self.ocr_provider is not None:
                try:
                    ocr_result = self.ocr_provider.extract(frame.path)
                except Exception:
                    ocr_result = None
                else:
                    if ocr_result and ocr_result.text.strip():
                        evidence_units.append(
                            EvidenceUnit(
                                asset_id=asset.asset_id,
                                span_ref='%s:ocr' % span_base,
                                content_type=ContentType.OCR,
                                content=ocr_result.text.strip(),
                                confidence=0.75,
                                tags=unique_preserve_order([
                                    'engine:%s' % ocr_result.engine,
                                    'source:%s' % frame.source,
                                ]),
                            )
                        )

            if self.analyzer is not None:
                try:
                    analysis = self.analyzer.analyze(
                        frame.path,
                        prompt='Describe the operationally relevant content of this video frame.',
                    )
                except Exception:
                    analysis = None
                else:
                    if analysis and analysis.summary.strip():
                        evidence_units.append(
                            EvidenceUnit(
                                asset_id=asset.asset_id,
                                span_ref='%s:scene' % span_base,
                                content_type=ContentType.SCENE,
                                content=analysis.summary.strip(),
                                confidence=0.70,
                                tags=unique_preserve_order(list(analysis.tags) + ['source:%s' % frame.source]),
                            )
                        )
        return frames

    def _collect_timeline_evidence(
        self,
        asset: Asset,
        evidence_units: list[EvidenceUnit],
        sampled_frames: list[SampledFrame],
        adapter_metadata: dict[str, object],
    ) -> None:
        parsed = self.video_parser.parse(frames=sampled_frames, evidence_units=evidence_units)
        for block in parsed.evidence_blocks:
            evidence_units.append(
                EvidenceUnit(
                    asset_id=asset.asset_id,
                    span_ref=block.span_ref,
                    content_type=block.content_type,
                    content=block.content,
                    confidence=block.confidence,
                    tags=unique_preserve_order(block.tags),
                )
            )
        adapter_metadata['scene_cluster_count'] = len(parsed.scene_clusters)
        adapter_metadata['scene_clusters'] = parsed.scene_clusters
        adapter_metadata['frame_event_count'] = parsed.frame_event_count
        adapter_metadata['subtitle_alignment_count'] = parsed.subtitle_alignment_count

    def _build_frame_span(self, index: int, frame: SampledFrame) -> str:
        if frame.timestamp_seconds is None:
            return 'frame:%04d' % index
        return 'frame:%04d@%.2fs' % (index, frame.timestamp_seconds)
