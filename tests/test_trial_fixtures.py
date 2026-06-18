from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.image import ImageAdapter
from omni_skill_pipeline.adapters.tabular import TabularAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.models import (
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
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult, SampledFrame, VideoMetadata
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class FixtureOCRProvider(object):
    def extract(self, image_path: Path) -> OCRResult:
        stem = image_path.stem.replace('-', ' ')
        return OCRResult(
            text=f"Fixture OCR: {stem}\nstatus: degraded",
            blocks=[
                OCRBlock(text=f"Fixture OCR: {stem}", confidence=0.91),
                OCRBlock(text="status: degraded", confidence=0.89),
            ],
            engine='fixture-ocr',
        )


class FixtureImageAnalyzer(object):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        return FrameAnalysis(
            image_path=image_path,
            summary=f"Fixture scene summary for {image_path.stem}.",
            tags=['fixture', 'scene', image_path.suffix.lower().lstrip('.')],
        )


class FixtureMediaProcessor(object):
    def probe(self, video_path: Path) -> VideoMetadata:
        return VideoMetadata(duration_seconds=9.0, width=640, height=360, fps=1.0, frame_count=9)

    def __init__(self, frame_source: Path) -> None:
        self.frame_source = frame_source

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        output = work_dir / 'fixture_audio.wav'
        output.write_bytes(b'RIFF\x24\x00\x00\x00WAVEfmt ')
        output.with_suffix('.srt').write_text(
            '\n'.join(
                [
                    '1',
                    '00:00:01,000 --> 00:00:03,000',
                    'Open release dashboard and verify GO gate.',
                    '',
                    '2',
                    '00:00:03,000 --> 00:00:05,000',
                    'Compare latency and error trends after rollout.',
                    '',
                    '3',
                    '00:00:05,000 --> 00:00:07,000',
                    'If regression persists, roll back and attach evidence.',
                ]
            ),
            encoding='utf-8',
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
        for index in range(1, min(max_frames, 2) + 1):
            target = work_dir / f'frame_{index:03d}.png'
            target.write_bytes(self.frame_source.read_bytes())
            frames.append(
                SampledFrame(
                    path=target,
                    source='scene' if index == 1 else 'timeline',
                    timestamp_seconds=float(index * 2),
                )
            )
        return frames


class TrialFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trial_root = REPO_ROOT / 'examples' / 'trial'
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.repository = FileArtifactRepository(self.workspace / 'drafts')
        self.ocr_provider = FixtureOCRProvider()
        self.image_analyzer = FixtureImageAnalyzer()

        audio_adapter = AudioAdapter()
        image_adapter = ImageAdapter(self.ocr_provider, self.image_analyzer)
        video_adapter = VideoAdapter(
            media_processor=FixtureMediaProcessor(self.trial_root / 'image' / 'service-latency-dashboard.png'),
            audio_adapter=audio_adapter,
            ocr_provider=self.ocr_provider,
            analyzer=self.image_analyzer,
            default_interval_seconds=3,
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

    def test_manifest_example_assets_exist_for_all_modalities(self) -> None:
        manifest_root = REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'trial-manifests'
        manifest_files = [
            manifest_root / 'trial-sample-text.example.json',
            manifest_root / 'trial-sample-audio.example.json',
            manifest_root / 'trial-sample-image.example.json',
            manifest_root / 'trial-sample-video.example.json',
            manifest_root / 'trial-sample-tabular.example.json',
            manifest_root / 'trial-sample-mixed-corpus.example.json',
        ]

        for manifest_path in manifest_files:
            payload = json.loads(manifest_path.read_text(encoding='utf-8'))
            for sample in payload.get('samples', []):
                for asset in sample.get('asset_list', []):
                    uri = str(asset.get('uri', '')).strip()
                    self.assertTrue(uri, f'{manifest_path} has empty asset uri')
                    asset_path = REPO_ROOT / uri
                    self.assertTrue(asset_path.exists(), f'Missing fixture asset: {asset_path}')

    def test_single_asset_modalities_run_offline_with_fixture_stubs(self) -> None:
        goal = DistillGoal.from_dict({'domain': 'controlled_trial'})

        text_bundle = self.service.distill_text(
            TextDistillRequest(
                title='Trial Text Fixture',
                file_path=str(self.trial_root / 'text' / 'slow-query-notes.md'),
                goal=goal,
            )
        )
        self.assertTrue(text_bundle.evidence_units)

        audio_bundle = self.service.distill_audio(
            AudioDistillRequest(
                title='Trial Audio Fixture',
                audio_path=str(self.trial_root / 'audio' / 'incident-review-call.wav'),
                goal=goal,
            )
        )
        self.assertTrue(audio_bundle.evidence_units)

        image_bundle = self.service.distill_image(
            ImageDistillRequest(
                image_path=str(self.trial_root / 'image' / 'service-latency-dashboard.png'),
                title='Trial Image Fixture',
                goal=goal,
            )
        )
        self.assertTrue(image_bundle.evidence_units)

        tabular_bundle = self.service.distill_tabular(
            TabularDistillRequest(
                file_path=str(self.trial_root / 'tabular' / 'latency-error-report.csv'),
                title='Trial Tabular Fixture',
                time_column='timestamp',
                value_columns=['latency_ms', 'error_rate'],
                entity_columns=['service'],
                goal=goal,
            )
        )
        self.assertTrue(tabular_bundle.evidence_units)

        video_bundle = self.service.distill_video(
            VideoDistillRequest(
                video_path=str(self.trial_root / 'video' / 'feature-release-walkthrough.mp4'),
                title='Trial Video Fixture',
                goal=goal,
            )
        )
        self.assertTrue(video_bundle.evidence_units)
        self.assertTrue(any(unit.content_type.value == 'speech' for unit in video_bundle.evidence_units))
        self.assertTrue(any(unit.content_type.value == 'ocr' for unit in video_bundle.evidence_units))

    def test_mixed_corpus_fixture_bundle_runs_offline(self) -> None:
        goal = DistillGoal.from_dict({'domain': 'incident_response'})
        request = CorpusDistillRequest(
            name='Trial Mixed Corpus Fixture',
            goal=goal,
            assets=[
                CorpusAssetInput(
                    source_uri=str(self.trial_root / 'mixed' / 'incident-postmortem.md'),
                    modality=Modality.TEXT,
                    role='primary',
                    title_hint='Incident Postmortem',
                ),
                CorpusAssetInput(
                    source_uri=str(self.trial_root / 'mixed' / 'incident-dashboard.png'),
                    modality=Modality.IMAGE,
                    role='context',
                    title_hint='Incident Dashboard',
                ),
                CorpusAssetInput(
                    source_uri=str(self.trial_root / 'mixed' / 'incident-review-transcript.md'),
                    modality=Modality.TEXT,
                    role='context',
                    title_hint='Incident Review Transcript',
                ),
            ],
            tags=['fixture', 'controlled_trial'],
        )

        bundle = self.service.distill_corpus(request)
        self.assertIsNotNone(bundle.corpus)
        self.assertEqual(len(bundle.corpus.assets), 3)
        self.assertGreaterEqual(len(bundle.evidence_units), 3)
        source_modalities = {item.value for item in bundle.skill_graph.source_modalities}
        self.assertIn('text', source_modalities)
        self.assertIn('image', source_modalities)


if __name__ == '__main__':
    unittest.main()
