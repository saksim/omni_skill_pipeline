from __future__ import annotations

from pathlib import Path

from PIL import Image

from omni_skill_pipeline.exceptions import ProviderUnavailableError
from omni_skill_pipeline.interfaces import ImageAnalyzer, OCRProvider
from omni_skill_pipeline.models import Asset, ContentType, EvidenceUnit, ImageDistillRequest, LoadedAsset, Modality
from omni_skill_pipeline.utils import unique_preserve_order


class ImageAdapter(object):
    def __init__(self, ocr_provider: OCRProvider | None = None, analyzer: ImageAnalyzer | None = None) -> None:
        self.ocr_provider = ocr_provider
        self.analyzer = analyzer

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

        if self.ocr_provider is not None:
            try:
                ocr_result = self.ocr_provider.extract(image_path)
            except ProviderUnavailableError:
                ocr_result = None
            except Exception:
                ocr_result = None
            else:
                if ocr_result and ocr_result.text.strip():
                    evidence_units.append(
                        EvidenceUnit(
                            asset_id=asset.asset_id,
                            span_ref='image:ocr:0001',
                            content_type=ContentType.OCR,
                            content=ocr_result.text.strip(),
                            confidence=0.78,
                            tags=['engine:%s' % ocr_result.engine],
                        )
                    )

        if self.analyzer is not None:
            try:
                analysis = self.analyzer.analyze(image_path)
            except ProviderUnavailableError:
                analysis = None
            except Exception:
                analysis = None
            else:
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

        if not evidence_units:
            raise ValueError('Image adapter produced no evidence. Configure OCR or image analysis providers.')

        return LoadedAsset(
            asset=asset,
            evidence_units=evidence_units,
            title_hint=title_hint,
            adapter_metadata={'frame_count': 1},
        )

    def _build_metadata(self, image_path: Path) -> dict[str, object]:
        with Image.open(image_path) as image:
            return {
                'filename': image_path.name,
                'width': image.width,
                'height': image.height,
                'format': image.format,
            }
