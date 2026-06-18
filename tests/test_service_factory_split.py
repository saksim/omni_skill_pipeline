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
            controlled_trial_review_mode=True,
            controlled_trial_review_reason_code='controlled_trial_requires_review',
            portable_skill_markdown_line_limit=220,
            artifact_repository_mode='file',
            postgres_repository_dsn=None,
            dual_write_continue_on_secondary_error=True,
            dual_write_secondary_prefix='secondary_',
            governance_ledger_dir=Path('/virtual/repo/skills/drafts/governance'),
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
            patch.object(factory_module, '_build_publication_orchestrator', return_value='publication-orchestrator') as publication_orchestrator_cls,
            patch.object(factory_module, 'ReviewPolicy', return_value='review-policy') as review_policy_cls,
            patch.object(factory_module, 'GovernanceLedger', return_value='governance-ledger') as governance_ledger_cls,
            patch.object(factory_module, 'DistillationService', return_value='service-instance') as service_cls,
        ):
            result = factory_module.build_service(repo_root='repo-root-marker')

        repo_cls.assert_called_once_with(settings.draft_dir)
        service_cls.assert_called_once_with(
            repository='repo',
            governance_ledger='governance-ledger',
            text_adapter='text-adapter',
            audio_adapter='audio-adapter',
            image_adapter='image-adapter',
            tabular_adapter='tabular-adapter',
            video_adapter='video-adapter',
            insight_extractor='insight-extractor',
            skill_composer='skill-composer',
            publication_orchestrator='publication-orchestrator',
            review_policy='review-policy',
        )
        governance_ledger_cls.assert_called_once_with(settings.governance_ledger_dir)
        publication_orchestrator_cls.assert_called_once_with(
            insight_extractor='insight-extractor',
            portable_skill_line_limit=220,
        )
        review_policy_cls.assert_called_once_with(
            force_review_mode=True,
            force_review_reason_code='controlled_trial_requires_review',
        )
        self.assertEqual(result, 'service-instance')

    def test_build_artifact_repository_file_mode(self) -> None:
        factory_module = importlib.import_module('omni_skill_pipeline.service_factory')
        factory_module = importlib.reload(factory_module)
        settings = SimpleNamespace(
            artifact_repository_mode='file',
            draft_dir=Path('/virtual/drafts'),
        )
        with patch.object(factory_module, 'FileArtifactRepository', return_value='file-repo') as file_repo_cls:
            repository = factory_module._build_artifact_repository(settings)
        file_repo_cls.assert_called_once_with(settings.draft_dir)
        self.assertEqual(repository, 'file-repo')

    def test_build_artifact_repository_postgres_mode_requires_dsn(self) -> None:
        factory_module = importlib.import_module('omni_skill_pipeline.service_factory')
        factory_module = importlib.reload(factory_module)
        settings = SimpleNamespace(
            artifact_repository_mode='postgres',
            draft_dir=Path('/virtual/drafts'),
            postgres_repository_dsn='',
        )
        with self.assertRaises(ValueError):
            factory_module._build_artifact_repository(settings)

    def test_build_artifact_repository_postgres_mode_uses_postgres_repository(self) -> None:
        factory_module = importlib.import_module('omni_skill_pipeline.service_factory')
        factory_module = importlib.reload(factory_module)
        settings = SimpleNamespace(
            artifact_repository_mode='postgres',
            draft_dir=Path('/virtual/drafts'),
            postgres_repository_dsn='postgresql://example',
        )
        with (
            patch.object(factory_module, 'FileArtifactRepository', return_value='file-repo'),
            patch.object(factory_module, 'PostgresRepository', return_value='pg-repo') as pg_repo_cls,
        ):
            repository = factory_module._build_artifact_repository(settings)
        pg_repo_cls.assert_called_once_with('postgresql://example')
        self.assertEqual(repository, 'pg-repo')

    def test_build_artifact_repository_dual_write_mode_uses_postgres_primary(self) -> None:
        factory_module = importlib.import_module('omni_skill_pipeline.service_factory')
        factory_module = importlib.reload(factory_module)
        settings = SimpleNamespace(
            artifact_repository_mode='dual_write',
            draft_dir=Path('/virtual/drafts'),
            postgres_repository_dsn='postgresql://example',
            dual_write_continue_on_secondary_error=False,
            dual_write_secondary_prefix='mirror_',
        )
        with (
            patch.object(factory_module, 'FileArtifactRepository', return_value='file-repo') as file_repo_cls,
            patch.object(factory_module, 'PostgresRepository', return_value='pg-repo') as pg_repo_cls,
            patch.object(factory_module, 'DualWriteArtifactRepository', return_value='dual-repo') as dual_repo_cls,
        ):
            repository = factory_module._build_artifact_repository(settings)
        file_repo_cls.assert_called_once_with(settings.draft_dir)
        pg_repo_cls.assert_called_once_with('postgresql://example')
        dual_repo_cls.assert_called_once_with(
            primary='pg-repo',
            secondary='file-repo',
            continue_on_secondary_error=False,
            secondary_prefix='mirror_',
        )
        self.assertEqual(repository, 'dual-repo')


if __name__ == '__main__':
    unittest.main()
