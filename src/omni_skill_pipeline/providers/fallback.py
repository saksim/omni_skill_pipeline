from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from omni_skill_pipeline.exceptions import ProviderExecutionError, ProviderUnavailableError
from omni_skill_pipeline.interfaces import AudioTranscriber, ImageAnalyzer, OCRProvider, SkillComposer
from omni_skill_pipeline.models import DistillGoal, EvidenceUnit, Insight, Modality, SkillDocument
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRResult, TranscriptionResult


class FallbackAudioTranscriber(object):
    def __init__(self, providers: Iterable[AudioTranscriber]) -> None:
        self.providers = list(providers)

    def transcribe(self, audio_path: Path, *, language: str | None = None, prompt: str | None = None) -> TranscriptionResult:
        errors = []
        for provider in self.providers:
            try:
                return provider.transcribe(audio_path, language=language, prompt=prompt)
            except (ProviderUnavailableError, ProviderExecutionError) as exc:
                errors.append('%s: %s' % (provider.__class__.__name__, exc))
        raise ProviderUnavailableError('No audio transcriber succeeded: %s' % '; '.join(errors or ['none']))


class FallbackOCRProvider(object):
    def __init__(self, providers: Iterable[OCRProvider]) -> None:
        self.providers = list(providers)

    def extract(self, image_path: Path) -> OCRResult:
        errors = []
        for provider in self.providers:
            try:
                return provider.extract(image_path)
            except (ProviderUnavailableError, ProviderExecutionError) as exc:
                errors.append('%s: %s' % (provider.__class__.__name__, exc))
        raise ProviderUnavailableError('No OCR provider succeeded: %s' % '; '.join(errors or ['none']))


class FallbackImageAnalyzer(object):
    def __init__(self, analyzers: Iterable[ImageAnalyzer]) -> None:
        self.analyzers = list(analyzers)

    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        errors = []
        for analyzer in self.analyzers:
            try:
                return analyzer.analyze(image_path, prompt=prompt)
            except (ProviderUnavailableError, ProviderExecutionError) as exc:
                errors.append('%s: %s' % (analyzer.__class__.__name__, exc))
        raise ProviderUnavailableError('No image analyzer succeeded: %s' % '; '.join(errors or ['none']))


class FallbackSkillComposer(object):
    def __init__(self, composers: Iterable[SkillComposer]) -> None:
        self.composers = list(composers)

    def compose(
        self,
        title_hint: str,
        goal: DistillGoal,
        modality: Modality,
        evidence_units: Sequence[EvidenceUnit],
        insights: Sequence[Insight],
    ) -> SkillDocument:
        errors = []
        for composer in self.composers:
            try:
                return composer.compose(title_hint, goal, modality, evidence_units, insights)
            except (ProviderUnavailableError, ProviderExecutionError, ValueError) as exc:
                errors.append('%s: %s' % (composer.__class__.__name__, exc))
        raise ProviderUnavailableError('No skill composer succeeded: %s' % '; '.join(errors or ['none']))


class NullImageAnalyzer(object):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        raise ProviderUnavailableError('No image analyzer configured.')
