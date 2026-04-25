from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class ServiceFactorySplitTests(unittest.TestCase):
    def test_service_build_service_delegates_to_service_factory(self) -> None:
        service_module = importlib.import_module('omni_skill_pipeline.service')
        service_module = importlib.reload(service_module)

        sentinel = object()
        with patch('omni_skill_pipeline.service_factory.build_service', return_value=sentinel) as factory_mock:
            result = service_module.build_service('repo-root-marker')

        factory_mock.assert_called_once_with(repo_root='repo-root-marker')
        self.assertIs(result, sentinel)
        self.assertFalse(hasattr(service_module, '_build_audio_adapter'))
        self.assertFalse(hasattr(service_module, '_build_image_capabilities'))
        self.assertFalse(hasattr(service_module, '_build_skill_composer'))

    def test_service_factory_build_service_keeps_composition_root(self) -> None:
        factory_module = importlib.import_module('omni_skill_pipeline.service_factory')
        factory_module = importlib.reload(factory_module)

        settings = SimpleNamespace(
            draft_dir=Path('/virtual/drafts'),
            ffmpeg_bin='ffmpeg',
            ffprobe_bin='ffprobe',
            video_scene_threshold=0.32,
            video_frame_dedupe_distance=5,
            keyframe_interval_seconds=8,
            max_keyframes=6,
            repo_root=Path('/virtual/repo'),
            template_path=Path('/virtual/template.md'),
        )

        with (
            patch.object(factory_module, 'load_settings', return_value=settings),
            patch.object(factory_module, 'FileArtifactRepository', return_value='repo') as repo_cls,
            patch.object(factory_module, '_build_audio_adapter', return_value='audio-adapter'),
            patch.object(factory_module, '_build_image_capabilities', return_value=('ocr-provider', 'image-analyzer')),
            patch.object(factory_module, 'FFmpegMediaProcessor', return_value='media-processor'),
            patch.object(factory_module, 'VideoAdapter', return_value='video-adapter'),
            patch.object(factory_module, 'TextAdapter', return_value='text-adapter'),
            patch.object(factory_module, 'ImageAdapter', return_value='image-adapter'),
            patch.object(factory_module, 'TabularAdapter', return_value='tabular-adapter'),
            patch.object(factory_module, 'HeuristicInsightExtractor', return_value='insight-extractor'),
            patch.object(factory_module, '_build_skill_composer', return_value='skill-composer'),
            patch.object(factory_module, 'DistillationService', return_value='service-instance') as service_cls,
        ):
            result = factory_module.build_service(repo_root='repo-root-marker')

        repo_cls.assert_called_once_with(settings.draft_dir)
        service_cls.assert_called_once_with(
            repository='repo',
            text_adapter='text-adapter',
            audio_adapter='audio-adapter',
            image_adapter='image-adapter',
            tabular_adapter='tabular-adapter',
            video_adapter='video-adapter',
            insight_extractor='insight-extractor',
            skill_composer='skill-composer',
        )
        self.assertEqual(result, 'service-instance')


if __name__ == '__main__':
    unittest.main()
