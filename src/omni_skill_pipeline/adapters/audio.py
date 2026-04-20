from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from omni_skill_pipeline.extraction.modality.audio_parser import AudioSemanticParser
from omni_skill_pipeline.interfaces import AudioTranscriber
from omni_skill_pipeline.models import Asset, AudioDistillRequest, ContentType, EvidenceUnit, LoadedAsset, Modality
from omni_skill_pipeline.providers.base import TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.utils import read_text_file, split_paragraphs, unique_preserve_order


class AudioAdapter(object):
    SIDECAR_SUFFIXES = ('.txt', '.md', '.srt', '.json')

    def __init__(
        self,
        transcriber: AudioTranscriber | None = None,
        semantic_parser: AudioSemanticParser | None = None,
    ) -> None:
        self.transcriber = transcriber
        self.semantic_parser = semantic_parser or AudioSemanticParser()

    def load(self, request: AudioDistillRequest) -> LoadedAsset:
        request.validate()
        transcript_result, source_uri, transcript_source = self._resolve_transcript(request)
        title_hint = request.title or self._derive_title_hint(request, transcript_source)
        asset = Asset(
            modality=Modality.AUDIO,
            source_uri=source_uri,
            metadata={'transcript_source': transcript_source, 'language': transcript_result.language},
        )
        evidence_units = self._build_evidence(asset.asset_id, transcript_result)
        semantic_counts = self._collect_utterance_act_counts(evidence_units)
        return LoadedAsset(
            asset=asset,
            evidence_units=evidence_units,
            title_hint=title_hint,
            adapter_metadata={
                'transcript_source': transcript_source,
                'utterance_act_counts': semantic_counts,
            },
        )

    def _resolve_transcript(self, request: AudioDistillRequest) -> tuple[TranscriptionResult, str, str]:
        if request.transcript:
            return self._parse_transcript_payload(request.transcript), request.audio_path or 'inline://transcript', 'inline transcript'

        if request.transcript_path:
            transcript_path = Path(request.transcript_path)
            return (
                self._parse_transcript_payload(self._load_transcript_path(transcript_path)),
                str(transcript_path.resolve()),
                transcript_path.name,
            )

        if request.audio_path:
            audio_path = Path(request.audio_path)
            sidecar = self._find_sidecar(audio_path)
            if sidecar:
                return (
                    self._parse_transcript_payload(self._load_transcript_path(sidecar)),
                    str(audio_path.resolve()),
                    sidecar.name,
                )
            if self.transcriber is not None:
                result = self.transcriber.transcribe(audio_path, language=request.language, prompt=request.prompt)
                return result, str(audio_path.resolve()), 'provider:%s' % (result.model_name or self.transcriber.__class__.__name__)

        raise ValueError('Audio processing requires transcript input or a configured transcriber.')

    def _load_transcript_path(self, path: Path) -> object:
        suffix = path.suffix.lower()
        if suffix == '.json':
            return json.loads(path.read_text(encoding='utf-8'))
        return read_text_file(path)

    def _find_sidecar(self, audio_path: Path) -> Optional[Path]:
        for suffix in self.SIDECAR_SUFFIXES:
            candidate = audio_path.with_suffix(suffix)
            if candidate.exists():
                return candidate
        return None

    def _derive_title_hint(self, request: AudioDistillRequest, transcript_name: str) -> str:
        if request.audio_path:
            return Path(request.audio_path).stem.replace('_', ' ')
        if request.transcript_path:
            return Path(request.transcript_path).stem.replace('_', ' ')
        return transcript_name

    def _parse_transcript_payload(self, transcript_payload: object) -> TranscriptionResult:
        if isinstance(transcript_payload, TranscriptionResult):
            return transcript_payload
        if isinstance(transcript_payload, dict):
            segments = transcript_payload.get('segments', [])
            return self._segments_to_result(segments, str(transcript_payload.get('text', '')))
        if isinstance(transcript_payload, list):
            return self._segments_to_result(transcript_payload, '')
        transcript_text = str(transcript_payload)
        if self._looks_like_srt(transcript_text):
            return self._segments_to_result(self._parse_srt(transcript_text), transcript_text)
        segments = self._parse_transcript_lines(transcript_text)
        if segments:
            return self._segments_to_result(segments, transcript_text)
        paragraphs = split_paragraphs(transcript_text)
        return TranscriptionResult(
            text=transcript_text.strip(),
            segments=[TranscriptSegment(text=paragraph, confidence=0.72) for paragraph in paragraphs],
        )

    def _segments_to_result(self, segments: List[Dict[str, object]], fallback_text: str) -> TranscriptionResult:
        normalized_segments = []
        texts = []
        for segment in segments:
            text = str(segment.get('text', '')).strip()
            if not text:
                continue
            normalized_segments.append(
                TranscriptSegment(
                    text=text,
                    start=self._to_float(segment.get('start') or segment.get('timestamp')),
                    end=self._to_float(segment.get('end')),
                    speaker=self._none_if_blank(segment.get('speaker')),
                    confidence=float(segment.get('confidence', 0.82)),
                )
            )
            texts.append(text)
        full_text = '\n'.join(texts) if texts else fallback_text.strip()
        return TranscriptionResult(text=full_text, segments=normalized_segments)

    def _build_evidence(self, asset_id: str, transcript_result: TranscriptionResult) -> List[EvidenceUnit]:
        evidence_units = []
        if transcript_result.segments:
            for index, segment in enumerate(transcript_result.segments, start=1):
                start = 'segment:%04d' % index if segment.start is None else '%.2f' % segment.start
                end = None if segment.end is None else '%.2f' % segment.end
                span_ref = 'timestamp:%s' % start if end is None else 'timestamp:%s-%s' % (start, end)
                tags = []
                if segment.speaker:
                    tags.append('speaker:%s' % segment.speaker)
                semantics = self.semantic_parser.parse(segment.text, segment.speaker)
                tags.extend(semantics.tags)
                evidence_units.append(
                    EvidenceUnit(
                        asset_id=asset_id,
                        span_ref=span_ref,
                        content_type=ContentType.SPEECH,
                        content=segment.text,
                        speaker=segment.speaker,
                        confidence=segment.confidence or 0.82,
                        tags=unique_preserve_order(tags),
                    )
                )
            return evidence_units

        for index, paragraph in enumerate(split_paragraphs(transcript_result.text), start=1):
            semantics = self.semantic_parser.parse(paragraph, None)
            evidence_units.append(
                EvidenceUnit(
                    asset_id=asset_id,
                    span_ref='line:%04d' % index,
                    content_type=ContentType.SPEECH,
                    content=paragraph,
                    confidence=0.72,
                    tags=unique_preserve_order(semantics.tags),
                )
            )
        return evidence_units

    def _collect_utterance_act_counts(self, evidence_units: List[EvidenceUnit]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for unit in evidence_units:
            for tag in unit.tags:
                if not tag.startswith('utterance_act:'):
                    continue
                act = tag.split(':', 1)[1]
                counts[act] = counts.get(act, 0) + 1
        return counts

    def _parse_transcript_lines(self, transcript: str) -> List[Dict[str, object]]:
        pattern = re.compile(r'^(?:\[(?P<timestamp>[0-9:\-\. >]+)\]\s*)?(?:(?P<speaker>[^:\]]{1,40}):\s*)?(?P<text>.+)$')
        segments = []
        for line in transcript.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = pattern.match(stripped)
            if not match:
                continue
            segments.append(
                {
                    'timestamp': (match.group('timestamp') or '').strip() or None,
                    'speaker': (match.group('speaker') or '').strip() or None,
                    'text': match.group('text').strip(),
                }
            )
        return segments

    def _looks_like_srt(self, transcript: str) -> bool:
        lines = [line.strip() for line in transcript.strip().splitlines() if line.strip()]
        return bool(lines) and len(lines) >= 2 and lines[0].isdigit() and '-->' in lines[1]

    def _parse_srt(self, transcript: str) -> List[Dict[str, object]]:
        blocks = re.split(r'\n\s*\n', transcript.replace('\r\n', '\n'))
        segments = []
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if len(lines) < 3:
                continue
            start_end = lines[1]
            if '-->' not in start_end:
                continue
            start, end = [item.strip() for item in start_end.split('-->', 1)]
            segments.append({'start': self._parse_timestamp(start), 'end': self._parse_timestamp(end), 'text': ' '.join(lines[2:])})
        return segments

    def _parse_timestamp(self, raw_value: str) -> float:
        parts = raw_value.replace(',', '.').split(':')
        total = 0.0
        for item in parts:
            total = total * 60 + float(item)
        return total

    def _to_float(self, value: object) -> float | None:
        if value in (None, ''):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return self._parse_timestamp(str(value))
        except ValueError:
            return None

    def _none_if_blank(self, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None
