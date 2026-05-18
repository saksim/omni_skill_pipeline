from __future__ import annotations

from pathlib import Path

from PIL import Image

from omni_skill_pipeline.exceptions import ProviderUnavailableError
from omni_skill_pipeline.extraction.modality.image_parser import ImageStructureParser
from omni_skill_pipeline.interfaces import ImageAnalyzer, OCRProvider
from omni_skill_pipeline.models import Asset, ContentType, EvidenceUnit, ImageDistillRequest, LoadedAsset, Modality
from omni_skill_pipeline.utils import unique_preserve_order


class ImageAdapter(object):
    def __init__(
        self,
        ocr_provider: OCRProvider | None = None,
        analyzer: ImageAnalyzer | None = None,
        image_parser: ImageStructureParser | None = None,
    ) -> None:
        self.ocr_provider = ocr_provider
        self.analyzer = analyzer
        self.image_parser = image_parser or ImageStructureParser()

    def load(self, request: ImageDistillRequest) -> LoadedAsset:
        request.validate()
        image_path = Path(request.image_path)
        if not image_path.exists():
            raise FileNotFoundError(str(image_path))

        asset = Asset(
            modality=Modality.IMAGE,
            source_uri=str(image_path.resolve()),
            metadata=self._build_metadata(image_path),
        )
        title_hint = request.title or image_path.stem.replace('_', ' ')
        evidence_units = []
        adapter_metadata: dict[str, object] = {'frame_count': 1}
        provider_calls: list[dict[str, object]] = []

        if self.ocr_provider is not None:
            ocr_provider_name = self.ocr_provider.__class__.__name__
            try:
                ocr_result = self.ocr_provider.extract(image_path)
            except ProviderUnavailableError:
                ocr_result = None
                provider_calls.append(
                    self._provider_call_entry(
                        channel='image_ocr',
                        provider=ocr_provider_name,
                        calls=1,
                        successes=0,
                        failures=1,
                    )
                )
            except Exception:
                ocr_result = None
                provider_calls.append(
                    self._provider_call_entry(
                        channel='image_ocr',
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
                        channel='image_ocr',
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
                            span_ref='image:ocr:0001',
                            content_type=ContentType.OCR,
                            content=ocr_result.text.strip(),
                            confidence=0.78,
                            tags=['engine:%s' % ocr_result.engine, 'block:ocr_full'],
                        )
                    )
                    region_blocks = self.image_parser.parse_ocr_regions(ocr_result)
                    layout_roles = set()
                    for block in region_blocks:
                        for tag in block.tags:
                            if tag.startswith('layout_role:'):
                                layout_roles.add(tag)
                        evidence_units.append(
                            EvidenceUnit(
                                asset_id=asset.asset_id,
                                span_ref=block.span_ref,
                                content_type=block.content_type,
                                content=block.content,
                                confidence=block.confidence,
                                tags=unique_preserve_order(['engine:%s' % ocr_result.engine] + block.tags),
                            )
                        )
                    adapter_metadata['ocr_region_count'] = len(region_blocks)
                    adapter_metadata['ocr_layout_roles'] = sorted(layout_roles)

        if self.analyzer is not None:
            analyzer_name = self.analyzer.__class__.__name__
            try:
                analysis = self.analyzer.analyze(image_path)
            except ProviderUnavailableError:
                analysis = None
                provider_calls.append(
                    self._provider_call_entry(
                        channel='image_analysis',
                        provider=analyzer_name,
                        calls=1,
                        successes=0,
                        failures=1,
                    )
                )
            except Exception:
                analysis = None
                provider_calls.append(
                    self._provider_call_entry(
                        channel='image_analysis',
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
                        channel='image_analysis',
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
                            span_ref='image:scene:0001',
                            content_type=ContentType.SCENE,
                            content=analysis.summary.strip(),
                            confidence=0.72,
                            tags=unique_preserve_order(analysis.tags),
                        )
                    )
                    layout_blocks = self.image_parser.parse_layout_summary(analysis)
                    for block in layout_blocks:
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
                    adapter_metadata['layout_evidence_count'] = len(layout_blocks)

        if not evidence_units:
            raise ValueError('Image adapter produced no evidence. Configure OCR or image analysis providers.')
        if provider_calls:
            adapter_metadata['provider_calls'] = provider_calls

        return LoadedAsset(
            asset=asset,
            evidence_units=evidence_units,
            title_hint=title_hint,
            adapter_metadata=adapter_metadata,
        )

    def _build_metadata(self, image_path: Path) -> dict[str, object]:
        with Image.open(image_path) as image:
            return {
                'filename': image_path.name,
                'width': image.width,
                'height': image.height,
                'format': image.format,
            }

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
            'channel': channel,
            'provider': provider,
            'calls': int(calls),
            'successes': int(successes),
            'failures': int(failures),
        }
