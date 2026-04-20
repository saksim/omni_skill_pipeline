from __future__ import annotations

import shutil
import sys
import unittest
from uuid import uuid4
from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.image import ImageAdapter
from omni_skill_pipeline.adapters.tabular import TabularAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult, TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.providers.base import SampledFrame, VideoMetadata
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class FakeTranscriber(object):
    def transcribe(self, audio_path: Path, *, language: str | None = None, prompt: str | None = None) -> TranscriptionResult:
        return TranscriptionResult(
            text='Rebuild the incident timeline. If alerts duplicate, merge them. Verify recovery with error rate and latency.',
            segments=[
                TranscriptSegment(text='1. Rebuild the incident timeline.', start=0.0, end=3.0, confidence=0.91),
                TranscriptSegment(text='If alerts duplicate, merge them into one incident stream.', start=3.0, end=6.0, confidence=0.88),
                TranscriptSegment(text='Verify recovery with error rate and latency.', start=6.0, end=9.0, confidence=0.86),
            ],
            language=language,
            model_name='fake-transcriber',
        )


class FakeOCRProvider(object):
    def extract(self, image_path: Path) -> OCRResult:
        return OCRResult(
            text='Service status: degraded\nPrimary region: shanghai',
            blocks=[
                OCRBlock(text='Service status: degraded', confidence=0.9),
                OCRBlock(text='Primary region: shanghai', confidence=0.88),
            ],
            engine='fake-ocr',
        )


class FakeImageAnalyzer(object):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        return FrameAnalysis(
            image_path=image_path,
            summary='Dashboard frame shows a degraded service banner and a latency spike.',
            tags=['dashboard', 'latency'],
        )


class FakeMediaProcessor(object):
    def probe(self, video_path: Path) -> VideoMetadata:
        return VideoMetadata(duration_seconds=12.0, width=320, height=200, fps=1.0, frame_count=12)

    def __init__(self, frame_source: Path) -> None:
        self.frame_source = frame_source

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        output = work_dir / 'audio_track.mp3'
        output.write_bytes(b'fake-audio')
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
        frames = []
        for index in range(1, min(max_frames, 2) + 1):
            target = work_dir / ('frame_%03d.jpg' % index)
            target.write_bytes(self.frame_source.read_bytes())
            frames.append(
                SampledFrame(
                    path=target,
                    source='scene' if index == 1 else 'timeline',
                    timestamp_seconds=float(index),
                )
            )
        return frames


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.repository = FileArtifactRepository(self.workspace / 'drafts')
        self.fixture_image = self.workspace / 'fixture.png'
        self.fixture_video = self.workspace / 'fixture.mp4'
        self.fixture_video.write_bytes(b'fake-video')
        self._make_image(self.fixture_image)

        audio_adapter = AudioAdapter(transcriber=FakeTranscriber())
        image_adapter = ImageAdapter(FakeOCRProvider(), FakeImageAnalyzer())
        video_adapter = VideoAdapter(
            media_processor=FakeMediaProcessor(self.fixture_image),
            audio_adapter=audio_adapter,
            ocr_provider=FakeOCRProvider(),
            analyzer=FakeImageAnalyzer(),
            default_interval_seconds=5,
            default_max_keyframes=2,
            scratch_root=self.workspace / 'media_scratch',
        )
        self.service = DistillationService(
            repository=self.repository,
            text_adapter=TextAdapter(),
            audio_adapter=audio_adapter,
            image_adapter=image_adapter,
            tabular_adapter=TabularAdapter(),
            video_adapter=video_adapter,
            insight_extractor=HeuristicInsightExtractor(),
            skill_composer=HeuristicSkillComposer(),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def _make_image(self, path: Path) -> None:
        image = Image.new('RGB', (320, 200), color='white')
        draw = ImageDraw.Draw(image)
        draw.text((10, 30), 'Service degraded', fill='black')
        draw.text((10, 70), 'Region: shanghai', fill='black')
        image.save(path)

    def test_text_distillation_creates_artifacts(self) -> None:
        request = TextDistillRequest(
            title='PostgreSQL Slow Query Review',
            content='''
# PostgreSQL Slow Query Review

1. Capture the top slow queries from pg_stat_statements.
2. Compare execution plans before changing indexes.

If the query is I/O bound, review the missing indexes first.
Avoid adding overlapping indexes without measuring write amplification.
Verify the new plan with EXPLAIN ANALYZE and compare latency.
'''.strip(),
            goal=DistillGoal.from_dict({'domain': 'database'}),
        )
        bundle = self.service.distill_text(request)
        self.assertEqual(bundle.skill.name, 'PostgreSQL Slow Query Review')
        self.assertGreaterEqual(len(bundle.skill.steps), 2)
        self.assertTrue(bundle.skill.decision_rules)
        self.assertTrue(bundle.skill.anti_patterns)
        self.assertTrue(Path(bundle.artifacts['skill']).exists())

    def test_audio_distillation_uses_transcriber_when_transcript_missing(self) -> None:
        audio_path = self.workspace / 'incident.wav'
        audio_path.write_bytes(b'fake-wav')
        bundle = self.service.distill_audio(
            AudioDistillRequest(
                title='Incident Debrief',
                audio_path=str(audio_path),
                goal=DistillGoal.from_dict({'domain': 'ops'}),
            )
        )
        self.assertEqual(bundle.asset.modality.value, 'audio')
        self.assertGreaterEqual(len(bundle.evidence_units), 3)
        self.assertTrue(bundle.skill.verification)
        self.assertIn('provider:fake-transcriber', bundle.adapter_metadata['transcript_source'])

    def test_image_distillation_generates_ocr_and_scene_evidence(self) -> None:
        bundle = self.service.distill_image(
            ImageDistillRequest(
                image_path=str(self.fixture_image),
                title='Service Dashboard Snapshot',
                goal=DistillGoal.from_dict({'domain': 'observability'}),
            )
        )
        content_types = {unit.content_type.value for unit in bundle.evidence_units}
        self.assertIn('ocr', content_types)
        self.assertIn('scene', content_types)
        span_refs = {unit.span_ref for unit in bundle.evidence_units}
        self.assertTrue(any(span.startswith('image:region:') for span in span_refs))
        layout_tags = {tag for unit in bundle.evidence_units for tag in unit.tags if tag.startswith('layout_role:')}
        self.assertTrue(layout_tags)
        self.assertTrue(Path(bundle.artifacts['skill_markdown']).exists())

    def test_video_distillation_merges_audio_and_keyframe_evidence(self) -> None:
        bundle = self.service.distill_video(
            VideoDistillRequest(
                video_path=str(self.fixture_video),
                title='Incident Walkthrough',
                goal=DistillGoal.from_dict({'domain': 'incident_response'}),
            )
        )
        content_types = {unit.content_type.value for unit in bundle.evidence_units}
        self.assertIn('speech', content_types)
        self.assertIn('ocr', content_types)
        self.assertIn('scene', content_types)
        self.assertGreaterEqual(len(bundle.evidence_units), 5)


if __name__ == '__main__':
    unittest.main()
