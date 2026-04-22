from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from omni_skill_pipeline.exceptions import MediaProcessingError, ProviderUnavailableError
from omni_skill_pipeline.providers.base import SampledFrame, VideoMetadata


class FFmpegMediaProcessor(object):
    def __init__(
        self,
        *,
        binary: str = 'ffmpeg',
        probe_binary: str = 'ffprobe',
        scene_threshold: float = 0.32,
        dedupe_distance: int = 5,
    ) -> None:
        self.binary = binary
        self.probe_binary = probe_binary
        self.scene_threshold = scene_threshold
        self.dedupe_distance = dedupe_distance

    def probe(self, video_path: Path) -> VideoMetadata:
        executable = self._resolve_probe_binary()
        command = [
            executable,
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-show_entries',
            'stream=width,height,avg_frame_rate,nb_frames:format=duration',
            '-of',
            'json',
            str(video_path),
        ]
        process = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if process.returncode != 0:
            raise MediaProcessingError(process.stderr.strip() or 'ffprobe failed.')
        payload = json.loads(process.stdout or '{}')
        stream = (payload.get('streams') or [{}])[0]
        format_info = payload.get('format') or {}
        return VideoMetadata(
            duration_seconds=self._to_float(format_info.get('duration')),
            width=self._to_int(stream.get('width')),
            height=self._to_int(stream.get('height')),
            fps=self._parse_rate(stream.get('avg_frame_rate')),
            frame_count=self._to_int(stream.get('nb_frames')),
        )

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        executable = self._resolve_binary()
        output_path = work_dir / 'audio_track.mp3'
        command = [
            executable,
            '-y',
            '-i',
            str(video_path),
            '-vn',
            '-ac',
            '1',
            '-ar',
            '16000',
            str(output_path),
        ]
        self._run(command, 'audio extraction')
        if not output_path.exists():
            raise MediaProcessingError('ffmpeg finished without producing audio output.')
        return output_path

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
        metadata = self.probe(video_path)
        effective_interval = self._effective_interval(metadata.duration_seconds, interval_seconds, max_frames)
        threshold = self.scene_threshold if scene_threshold is None else scene_threshold
        dedupe_limit = self.dedupe_distance if dedupe_distance is None else dedupe_distance

        candidates = []
        candidates.extend(self._extract_scene_candidates(video_path, work_dir, threshold, max_frames=max_frames * 3))
        candidates.extend(self._extract_sampled_candidates(video_path, work_dir, effective_interval, max_frames=max_frames * 3))
        if not candidates:
            candidates.extend(self._extract_fallback_frames(video_path, work_dir, max_frames))

        deduped = self._dedupe_frames(candidates, dedupe_limit)
        selected = self._select_distributed_frames(deduped, max_frames=max_frames, duration_seconds=metadata.duration_seconds)
        if not selected:
            raise MediaProcessingError('ffmpeg produced no keyframes.')
        return selected

    def _extract_scene_candidates(
        self,
        video_path: Path,
        work_dir: Path,
        threshold: float,
        *,
        max_frames: int,
    ) -> list[SampledFrame]:
        executable = self._resolve_binary()
        output_pattern = work_dir / 'scene_%03d.jpg'
        command = [
            executable,
            '-y',
            '-i',
            str(video_path),
            '-vf',
            "select='gt(scene,%s)',showinfo" % threshold,
            '-vsync',
            'vfr',
            '-frames:v',
            str(max(1, max_frames)),
            str(output_pattern),
        ]
        process = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if process.returncode != 0:
            return []
        files = sorted(work_dir.glob('scene_*.jpg'))
        timestamps = self._parse_showinfo_timestamps(process.stderr)
        scene_scores = self._parse_showinfo_scene_scores(process.stderr)
        return self._build_frames(files, timestamps, source='scene', scene_scores=scene_scores)

    def _extract_sampled_candidates(
        self,
        video_path: Path,
        work_dir: Path,
        interval_seconds: int,
        *,
        max_frames: int,
    ) -> list[SampledFrame]:
        executable = self._resolve_binary()
        output_pattern = work_dir / 'sample_%03d.jpg'
        command = [
            executable,
            '-y',
            '-i',
            str(video_path),
            '-vf',
            'fps=1/%s,showinfo' % max(1, interval_seconds),
            '-frames:v',
            str(max(1, max_frames)),
            str(output_pattern),
        ]
        process = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if process.returncode != 0:
            return []
        files = sorted(work_dir.glob('sample_*.jpg'))
        timestamps = self._parse_showinfo_timestamps(process.stderr)
        return self._build_frames(files, timestamps, source='timeline')

    def _extract_fallback_frames(self, video_path: Path, work_dir: Path, max_frames: int) -> list[SampledFrame]:
        executable = self._resolve_binary()
        output_pattern = work_dir / 'fallback_%03d.jpg'
        command = [
            executable,
            '-y',
            '-i',
            str(video_path),
            '-frames:v',
            str(max(1, max_frames)),
            str(output_pattern),
        ]
        process = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if process.returncode != 0:
            return []
        files = sorted(work_dir.glob('fallback_*.jpg'))
        return self._build_frames(files, [], source='fallback')

    def _build_frames(
        self,
        files: list[Path],
        timestamps: list[float],
        *,
        source: str,
        scene_scores: list[float] | None = None,
    ) -> list[SampledFrame]:
        frames = []
        for index, file_path in enumerate(files):
            timestamp = timestamps[index] if index < len(timestamps) else None
            scene_score = scene_scores[index] if scene_scores is not None and index < len(scene_scores) else None
            frames.append(SampledFrame(path=file_path, source=source, timestamp_seconds=timestamp, scene_score=scene_score))
        return frames

    def _dedupe_frames(self, frames: list[SampledFrame], dedupe_distance: int) -> list[SampledFrame]:
        kept: list[SampledFrame] = []
        for frame in sorted(frames, key=self._frame_sort_key):
            frame_hash = self._average_hash(frame.path)
            frame.dedupe_hash = frame_hash
            duplicate = False
            for existing in kept[-3:]:
                if existing.dedupe_hash is None:
                    continue
                if self._hamming_distance(frame_hash, existing.dedupe_hash) <= dedupe_distance:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(frame)
        return kept

    def _select_distributed_frames(
        self,
        frames: list[SampledFrame],
        *,
        max_frames: int,
        duration_seconds: float | None,
    ) -> list[SampledFrame]:
        if len(frames) <= max_frames:
            return frames
        ordered = sorted(frames, key=self._frame_sort_key)
        if not duration_seconds or duration_seconds <= 0:
            return ordered[:max_frames]

        bucket_size = duration_seconds / max_frames
        selected: list[SampledFrame] = []
        used_paths: set[str] = set()
        for bucket_index in range(max_frames):
            bucket_start = bucket_index * bucket_size
            bucket_end = duration_seconds + 1e-9 if bucket_index == max_frames - 1 else (bucket_index + 1) * bucket_size
            bucket_frames = [
                frame for frame in ordered
                if str(frame.path) not in used_paths
                and frame.timestamp_seconds is not None
                and bucket_start <= frame.timestamp_seconds < bucket_end
            ]
            if bucket_frames:
                chosen = next((frame for frame in bucket_frames if frame.source == 'scene'), bucket_frames[0])
                selected.append(chosen)
                used_paths.add(str(chosen.path))

        if len(selected) < max_frames:
            for frame in ordered:
                if str(frame.path) in used_paths:
                    continue
                selected.append(frame)
                used_paths.add(str(frame.path))
                if len(selected) == max_frames:
                    break

        return sorted(selected, key=self._frame_sort_key)[:max_frames]

    def _effective_interval(self, duration_seconds: float | None, base_interval: int, max_frames: int) -> int:
        if not duration_seconds or duration_seconds <= 0:
            return max(1, base_interval)
        adaptive = int(math.ceil(duration_seconds / max(1, max_frames)))
        return max(1, base_interval, adaptive)

    def _average_hash(self, image_path: Path) -> int:
        with Image.open(image_path) as image:
            pixels = image.convert('L').resize((8, 8))
            values = list(pixels.getdata())
        threshold = sum(values) / len(values)
        bits = 0
        for value in values:
            bits = (bits << 1) | int(value >= threshold)
        return bits

    def _hamming_distance(self, left: int, right: int) -> int:
        return (left ^ right).bit_count()

    def _parse_showinfo_timestamps(self, stderr_output: str) -> list[float]:
        timestamps: list[float] = []
        for line in stderr_output.splitlines():
            marker = 'pts_time:'
            if marker not in line:
                continue
            try:
                raw_value = line.split(marker, 1)[1].split(' ', 1)[0].strip()
                timestamps.append(float(raw_value))
            except ValueError:
                continue
        return timestamps

    def _parse_showinfo_scene_scores(self, stderr_output: str) -> list[float]:
        scores: list[float] = []
        scene_re = re.compile(r'(?:scene(?:_score)?|lavfi\.scene_score)\s*[:=]\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
        for line in stderr_output.splitlines():
            match = scene_re.search(line)
            if match is None:
                continue
            try:
                scores.append(float(match.group(1)))
            except ValueError:
                continue
        return scores

    def _frame_sort_key(self, frame: SampledFrame) -> tuple[float, int, str]:
        timestamp = frame.timestamp_seconds if frame.timestamp_seconds is not None else float('inf')
        source_rank = {'scene': 0, 'timeline': 1, 'fallback': 2}.get(frame.source, 3)
        return (timestamp, source_rank, str(frame.path))

    def _resolve_binary(self) -> str:
        executable = shutil.which(self.binary) or (self.binary if Path(self.binary).exists() else None)
        if not executable:
            raise ProviderUnavailableError('ffmpeg binary not found: %s' % self.binary)
        return executable

    def _resolve_probe_binary(self) -> str:
        executable = shutil.which(self.probe_binary) or (self.probe_binary if Path(self.probe_binary).exists() else None)
        if executable:
            return executable
        ffmpeg_binary = self._resolve_binary()
        sibling = Path(ffmpeg_binary).with_name('ffprobe.exe' if Path(ffmpeg_binary).suffix.lower() == '.exe' else 'ffprobe')
        if sibling.exists():
            return str(sibling)
        raise ProviderUnavailableError('ffprobe binary not found: %s' % self.probe_binary)

    def _run(self, command: list[str], label: str) -> None:
        process = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if process.returncode != 0:
            message = process.stderr.strip() or process.stdout.strip() or '%s failed' % label
            raise MediaProcessingError(message)

    def _parse_rate(self, raw_value: object) -> float | None:
        if raw_value in (None, '', '0/0'):
            return None
        text = str(raw_value)
        if '/' in text:
            left, right = text.split('/', 1)
            try:
                numerator = float(left)
                denominator = float(right)
            except ValueError:
                return None
            if denominator == 0:
                return None
            return numerator / denominator
        try:
            return float(text)
        except ValueError:
            return None

    def _to_float(self, raw_value: object) -> float | None:
        if raw_value in (None, ''):
            return None
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, raw_value: object) -> int | None:
        if raw_value in (None, ''):
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None
