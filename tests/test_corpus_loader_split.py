from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.corpus_loader import DefaultCorpusLoader
from omni_skill_pipeline.extraction import EvidenceBuilder
from omni_skill_pipeline.models import (
    Asset,
    AudioDistillRequest,
    ContentType,
    CorpusAssetInput,
    CorpusDistillRequest,
    DistillGoal,
    EvidenceUnit,
    LoadedAsset,
    Modality,
    TextDistillRequest,
)


class DefaultCorpusLoaderTests(unittest.TestCase):
    def test_load_corpus_builds_requests_and_merges_metadata(self) -> None:
        text_asset = Asset(modality=Modality.TEXT, source_uri='memory://text', metadata={'origin': 'adapter-text'})
        text_evidence = EvidenceUnit(
            asset_id=text_asset.asset_id,
            span_ref='text:line:1',
            content_type=ContentType.TEXT,
            content='timeline data',
        )
        text_loaded = LoadedAsset(
            asset=text_asset,
            evidence_units=[text_evidence],
            title_hint='Incident Notes',
            adapter_metadata={'provider': 'text-adapter'},
        )

        audio_asset = Asset(modality=Modality.AUDIO, source_uri='memory://audio', metadata={'origin': 'adapter-audio'})
        audio_evidence = EvidenceUnit(
            asset_id=audio_asset.asset_id,
            span_ref='audio:segment:1',
            content_type=ContentType.SPEECH,
            content='recover service before scaling',
        )
        audio_loaded = LoadedAsset(
            asset=audio_asset,
            evidence_units=[audio_evidence],
            title_hint='Audio Context',
            adapter_metadata={'provider': 'audio-adapter'},
        )

        text_adapter = Mock()
        text_adapter.load.return_value = text_loaded
        audio_adapter = Mock()
        audio_adapter.load.return_value = audio_loaded

        loader = DefaultCorpusLoader(
            text_adapter=text_adapter,
            audio_adapter=audio_adapter,
            image_adapter=Mock(),
            tabular_adapter=Mock(),
            video_adapter=Mock(),
            evidence_builder=EvidenceBuilder(),
        )

        request = CorpusDistillRequest(
            name='',
            assets=[
                CorpusAssetInput(
                    source_uri='file:///C:/tmp/incident-notes.md',
                    modality=Modality.TEXT,
                    role='primary',
                    metadata={'label': 'primary-input'},
                ),
                CorpusAssetInput(
                    source_uri='memory://incident.wav',
                    modality=Modality.AUDIO,
                    role='context',
                    metadata={'label': 'context-input'},
                ),
            ],
            goal=DistillGoal(domain='incident_response'),
            tags=['incident'],
            metadata={'owner': 'sre'},
        )

        loaded = loader.load_corpus(request)

        text_adapter.load.assert_called_once()
        audio_adapter.load.assert_called_once()

        text_request = text_adapter.load.call_args[0][0]
        audio_request = audio_adapter.load.call_args[0][0]
        self.assertIsInstance(text_request, TextDistillRequest)
        self.assertIsInstance(audio_request, AudioDistillRequest)
        self.assertEqual(text_request.file_path, 'C:/tmp/incident-notes.md')
        self.assertEqual(audio_request.audio_path, 'memory://incident.wav')

        self.assertEqual(loaded.corpus.name, 'Incident Notes')
        self.assertEqual(loaded.corpus.metadata['asset_count'], 2)
        self.assertEqual(loaded.corpus.metadata['owner'], 'sre')
        self.assertEqual(loaded.corpus.metadata['modalities'], ['text', 'audio'])
        self.assertEqual(len(loaded.evidence_units), 2)
        self.assertEqual(len(loaded.evidence_nodes), 2)

        first_asset_metadata = loaded.corpus.assets[0].metadata
        second_asset_metadata = loaded.corpus.assets[1].metadata
        self.assertEqual(first_asset_metadata['origin'], 'adapter-text')
        self.assertEqual(first_asset_metadata['label'], 'primary-input')
        self.assertEqual(second_asset_metadata['origin'], 'adapter-audio')
        self.assertEqual(second_asset_metadata['label'], 'context-input')
        self.assertEqual(loaded.adapter_metadata[text_asset.asset_id]['role'], 'primary')
        self.assertEqual(loaded.adapter_metadata[audio_asset.asset_id]['role'], 'context')


if __name__ == '__main__':
    unittest.main()
