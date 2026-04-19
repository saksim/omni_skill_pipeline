from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, Field

from omni_skill_pipeline.config import Settings
from omni_skill_pipeline.exceptions import ProviderExecutionError, ProviderUnavailableError
from omni_skill_pipeline.models import Audience, DistillGoal, EvidenceUnit, Insight, Modality, SkillDocument, SkillStep, SkillType
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult, TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.utils import unique_preserve_order

try:  # pragma: no cover - optional import boundary
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional import boundary
    OpenAI = None


class SkillDraftStepModel(BaseModel):
    step: int = Field(ge=1)
    action: str
    why: str = ''


class SkillDraftModel(BaseModel):
    name: str
    skill_type: str
    summary: str
    goal: str
    trigger: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    steps: list[SkillDraftStepModel] = Field(default_factory=list)
    decision_rules: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class OCRTextModel(BaseModel):
    text: str
    lines: list[str] = Field(default_factory=list)


class OpenAIClientMixin(object):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if OpenAI is None:
            raise ProviderUnavailableError('openai package is not installed.')
        if not settings.openai_api_key:
            raise ProviderUnavailableError('OPENAI_API_KEY is not configured.')
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


class OpenAIAudioTranscriber(OpenAIClientMixin):
    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        try:
            with audio_path.open('rb') as file_handle:
                response = self.client.audio.transcriptions.create(
                    file=file_handle,
                    model=self.settings.transcription_model,
                    language=language or self.settings.transcription_language,
                    prompt=prompt,
                    response_format='verbose_json',
                    timestamp_granularities=['segment'],
                )
        except Exception as exc:  # pragma: no cover - network boundary
            raise ProviderExecutionError('OpenAI transcription failed: %s' % exc) from exc

        segments = []
        for segment in getattr(response, 'segments', None) or []:
            segments.append(
                TranscriptSegment(
                    text=getattr(segment, 'text', '').strip(),
                    start=getattr(segment, 'start', None),
                    end=getattr(segment, 'end', None),
                    speaker=getattr(segment, 'speaker', None),
                    confidence=max(0.0, 1.0 - float(getattr(segment, 'no_speech_prob', 0.0) or 0.0)),
                )
            )
        text = getattr(response, 'text', '').strip()
        if not text:
            raise ProviderExecutionError('OpenAI transcription returned empty text.')
        return TranscriptionResult(
            text=text,
            segments=segments,
            language=getattr(response, 'language', None),
            model_name=self.settings.transcription_model,
            metadata={'duration': getattr(response, 'duration', None)},
        )


class OpenAIVisionAnalyzer(OpenAIClientMixin):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        input_payload = self._build_image_input(
            image_path,
            prompt or 'Describe the key visible entities, UI state, diagrams, and operational cues in this image.',
        )
        try:
            response = self.client.responses.create(model=self.settings.vision_model, input=input_payload)
        except Exception as exc:  # pragma: no cover - network boundary
            raise ProviderExecutionError('OpenAI vision analysis failed: %s' % exc) from exc

        summary = (response.output_text or '').strip()
        if not summary:
            raise ProviderExecutionError('OpenAI vision analysis returned empty text.')
        return FrameAnalysis(image_path=image_path, summary=summary, tags=[], metadata={'model': self.settings.vision_model})

    def extract(self, image_path: Path) -> OCRResult:
        input_payload = self._build_image_input(
            image_path,
            'Extract all readable text from this image. Return only the text content and preserve line breaks.',
        )
        try:
            response = self.client.responses.parse(
                model=self.settings.vision_model,
                input=input_payload,
                text_format=OCRTextModel,
            )
        except Exception as exc:  # pragma: no cover - network boundary
            raise ProviderExecutionError('OpenAI OCR failed: %s' % exc) from exc

        parsed = response.output_parsed
        if parsed is None or not parsed.text.strip():
            raise ProviderExecutionError('OpenAI OCR returned empty text.')
        lines = unique_preserve_order(parsed.lines or parsed.text.splitlines())
        return OCRResult(
            text=parsed.text.strip(),
            blocks=[OCRBlock(text=line, confidence=0.7) for line in lines if line.strip()],
            engine='openai_vision',
            metadata={'model': self.settings.vision_model},
        )

    def _build_image_input(self, image_path: Path, prompt: str) -> list[dict[str, object]]:
        media_type = mimetypes.guess_type(str(image_path))[0] or 'image/png'
        image_bytes = image_path.read_bytes()
        encoded = base64.b64encode(image_bytes).decode('ascii')
        return [
            {
                'role': 'user',
                'content': [
                    {'type': 'input_text', 'text': prompt},
                    {'type': 'input_image', 'image_url': 'data:%s;base64,%s' % (media_type, encoded)},
                ],
            }
        ]


class OpenAILLMSkillComposer(OpenAIClientMixin):
    def compose(
        self,
        title_hint: str,
        goal: DistillGoal,
        modality: Modality,
        evidence_units: Sequence[EvidenceUnit],
        insights: Sequence[Insight],
    ) -> SkillDocument:
        evidence_payload = self._build_evidence_payload(evidence_units, insights)
        instructions = self._build_instructions(goal, modality, title_hint)
        try:
            response = self.client.responses.parse(
                model=self.settings.llm_model,
                instructions=instructions,
                input=evidence_payload,
                text_format=SkillDraftModel,
            )
        except Exception as exc:  # pragma: no cover - network boundary
            raise ProviderExecutionError('OpenAI skill composition failed: %s' % exc) from exc

        parsed = response.output_parsed
        if parsed is None:
            raise ProviderExecutionError('OpenAI skill composer returned no structured output.')

        skill_type = self._coerce_skill_type(parsed.skill_type)
        steps = [
            SkillStep(step=item.step, action=item.action.strip(), why=item.why.strip())
            for item in parsed.steps
            if item.action.strip()
        ]
        if not steps:
            raise ValueError('LLM composer produced no executable steps.')

        return SkillDocument(
            name=parsed.name.strip() or title_hint.strip() or 'Untitled skill',
            goal=parsed.goal.strip(),
            source_modality=modality,
            skill_type=skill_type,
            audience=goal.audience,
            trigger=unique_preserve_order(parsed.trigger),
            inputs=unique_preserve_order(parsed.inputs),
            preconditions=unique_preserve_order(parsed.preconditions),
            steps=steps,
            decision_rules=unique_preserve_order(parsed.decision_rules),
            anti_patterns=unique_preserve_order(parsed.anti_patterns),
            verification=unique_preserve_order(parsed.verification),
            evidence_refs=unique_preserve_order(parsed.evidence_refs),
            confidence=0.82,
            summary=parsed.summary.strip(),
            tags=unique_preserve_order(parsed.tags + [goal.domain, modality.value, 'llm']),
        )

    def _build_instructions(self, goal: DistillGoal, modality: Modality, title_hint: str) -> str:
        lines = [
            'You are distilling evidence into a reusable SKILL artifact.',
            'Return only structured data matching the provided schema.',
            'Preserve traceability by citing evidence_ids in evidence_refs.',
            'Produce executable steps, not vague summaries.',
            'Avoid hallucinating facts not present in the evidence.',
            'Goal type: %s' % goal.goal_type.value,
            'Audience: %s' % goal.audience.value,
            'Rigor: %s' % goal.rigor.value,
            'Granularity: %s' % goal.granularity.value,
            'Domain: %s' % goal.domain,
            'Source modality: %s' % modality.value,
        ]
        if title_hint:
            lines.append('Title hint: %s' % title_hint)
        return '\n'.join(lines)

    def _build_evidence_payload(self, evidence_units: Sequence[EvidenceUnit], insights: Sequence[Insight]) -> list[dict[str, object]]:
        evidence_lines = []
        for unit in evidence_units[:18]:
            evidence_lines.append(
                '[%s|%s|%s] %s'
                % (unit.evidence_id, unit.span_ref, unit.content_type.value, unit.content[:700])
            )
        insight_lines = []
        for insight in insights[:18]:
            insight_lines.append(
                '[%s|%s] %s -> %s'
                % (insight.insight_id, insight.insight_type.value, ','.join(insight.evidence_refs), insight.summary[:400])
            )
        text = 'Evidence Units:\n%s\n\nInsights:\n%s' % (
            '\n'.join(evidence_lines),
            '\n'.join(insight_lines) if insight_lines else 'None',
        )
        return [{'role': 'user', 'content': [{'type': 'input_text', 'text': text}]}]

    def _coerce_skill_type(self, raw_value: str) -> SkillType:
        normalized = (raw_value or '').strip().lower()
        for member in SkillType:
            if member.value == normalized:
                return member
        return SkillType.PROCEDURE
