from __future__ import annotations

import json
import shutil
import time
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
        provider_calls: list[dict[str, object]] = [
            self._provider_call_entry(
                channel='video_probe',
                provider=self.media_processor.__class__.__name__,
                calls=1,
                successes=1,
                failures=0,
            )
        ]
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
            self._collect_audio_evidence(
                asset,
                request,
                video_path,
                work_dir,
                evidence_units,
                adapter_metadata,
                provider_calls,
            )
            sampled_frames = self._collect_frame_evidence(
                asset,
                request,
                video_path,
                work_dir,
                evidence_units,
                adapter_metadata,
                provider_calls,
            )
            self._collect_timeline_evidence(asset, evidence_units, sampled_frames, adapter_metadata)
        finally:
            self._cleanup_work_dir(work_dir, adapter_metadata)

        if not evidence_units:
            raise ValueError('Video adapter produced no evidence units.')
        if provider_calls:
            adapter_metadata['provider_calls'] = self._merge_provider_calls(provider_calls)

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
        provider_calls: list[dict[str, object]],
    ) -> None:
        try:
            audio_path = self.media_processor.extract_audio(video_path, work_dir)
        except (MediaProcessingError, ProviderUnavailableError):
            provider_calls.append(
                self._provider_call_entry(
                    channel='video_audio_extract',
                    provider=self.media_processor.__class__.__name__,
                    calls=1,
                    successes=0,
                    failures=1,
                )
            )
            return
        provider_calls.append(
            self._provider_call_entry(
                channel='video_audio_extract',
                provider=self.media_processor.__class__.__name__,
                calls=1,
                successes=1,
                failures=0,
            )
        )

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
            provider_calls.append(
                self._provider_call_entry(
                    channel='video_audio_parse',
                    provider=self.audio_adapter.__class__.__name__,
                    calls=1,
                    successes=0,
                    failures=1,
                )
            )
            return
        provider_calls.append(
            self._provider_call_entry(
                channel='video_audio_parse',
                provider=self.audio_adapter.__class__.__name__,
                calls=1,
                successes=1,
                failures=0,
            )
        )
        for item in loaded_audio.adapter_metadata.get('provider_calls', []):
            if not isinstance(item, dict):
                continue
            provider_calls.append(
                self._provider_call_entry(
                    channel='video_audio_%s' % str(item.get('channel', 'provider')).strip(),
                    provider=str(item.get('provider', '')).strip() or 'unknown',
                    calls=int(item.get('calls', 0) or 0),
                    successes=int(item.get('successes', 0) or 0),
                    failures=int(item.get('failures', 0) or 0),
                )
            )

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
        provider_calls: list[dict[str, object]],
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
        provider_calls.append(
            self._provider_call_entry(
                channel='video_keyframe_extract',
                provider=self.media_processor.__class__.__name__,
                calls=1,
                successes=1,
                failures=0,
            )
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
                ocr_provider_name = self.ocr_provider.__class__.__name__
                try:
                    ocr_result = self.ocr_provider.extract(frame.path)
                except Exception:
                    ocr_result = None
                    provider_calls.append(
                        self._provider_call_entry(
                            channel='video_frame_ocr',
                            provider=ocr_provider_name,
                            calls=1,
                            successes=0,
                            failures=1,
                        )
                    )
                else:
                    resolved_provider = (ocr_result.engine or '').strip() if ocr_result is not None else ''
                    provider_calls.append(
                        self._provider_call_entry(
                            channel='video_frame_ocr',
                            provider=resolved_provider or ocr_provider_name,
                            calls=1,
                            successes=1,
                            failures=0,
                        )
                    )
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
                analyzer_name = self.analyzer.__class__.__name__
                try:
                    analysis = self.analyzer.analyze(
                        frame.path,
                        prompt='Describe the operationally relevant content of this video frame.',
                    )
                except Exception:
                    analysis = None
                    provider_calls.append(
                        self._provider_call_entry(
                            channel='video_frame_analysis',
                            provider=analyzer_name,
                            calls=1,
                            successes=0,
                            failures=1,
                        )
                    )
                else:
                    resolved_provider = ''
                    if analysis is not None and isinstance(analysis.metadata, dict):
                        resolved_provider = str(analysis.metadata.get('model', '')).strip()
                    provider_calls.append(
                        self._provider_call_entry(
                            channel='video_frame_analysis',
                            provider=resolved_provider or analyzer_name,
                            calls=1,
                            successes=1,
                            failures=0,
                        )
                    )
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

    def _cleanup_work_dir(self, work_dir: Path, adapter_metadata: dict[str, object]) -> None:
        try:
            shutil.rmtree(work_dir)
        except OSError as exc:
            recovery_log = self.scratch_root / '.cleanup_recovery.log'
            recovery_entry = {
                'timestamp_epoch': int(time.time()),
                'work_dir': str(work_dir),
                'error': str(exc),
                'strategy': 'prune_tmp_media',
            }
            self._append_cleanup_recovery_entry(recovery_log, recovery_entry)
            adapter_metadata['scratch_cleanup'] = {
                'status': 'deferred',
                'work_dir': str(work_dir),
                'error': str(exc),
                'strategy': 'prune_tmp_media',
                'recovery_log': str(recovery_log),
                'recovery_command': 'python scripts/prune_tmp_media.py --retention-hours 24',
            }
            return

        adapter_metadata['scratch_cleanup'] = {
            'status': 'cleaned',
            'work_dir': str(work_dir),
        }

    def _append_cleanup_recovery_entry(self, log_path: Path, entry: dict[str, object]) -> None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(entry, ensure_ascii=True))
                handle.write('\n')
        except OSError:
            return

    def _build_frame_span(self, index: int, frame: SampledFrame) -> str:
        if frame.timestamp_seconds is None:
            return 'frame:%04d' % index
        return 'frame:%04d@%.2fs' % (index, frame.timestamp_seconds)

    def _provider_call_entry(
        self,
        *,
        channel: str,
        provider: str,
        calls: int,
        successes: int,
        failures: int,
    ) -> dict[str, object]:
        return {
            'channel': str(channel).strip() or 'provider',
            'provider': str(provider).strip() or 'unknown',
            'calls': max(0, int(calls)),
            'successes': max(0, int(successes)),
            'failures': max(0, int(failures)),
        }

    def _merge_provider_calls(self, provider_calls: list[dict[str, object]]) -> list[dict[str, object]]:
        merged: dict[tuple[str, str], dict[str, object]] = {}
        for item in provider_calls:
            if not isinstance(item, dict):
                continue
            channel = str(item.get('channel', '')).strip() or 'provider'
            provider = str(item.get('provider', '')).strip() or 'unknown'
            key = (channel, provider)
            if key not in merged:
                merged[key] = self._provider_call_entry(
                    channel=channel,
                    provider=provider,
                    calls=0,
                    successes=0,
                    failures=0,
                )
            merged[key]['calls'] += max(0, int(item.get('calls', 0) or 0))
            merged[key]['successes'] += max(0, int(item.get('successes', 0) or 0))
            merged[key]['failures'] += max(0, int(item.get('failures', 0) or 0))
        return sorted(merged.values(), key=lambda call: (str(call['channel']), str(call['provider'])))
