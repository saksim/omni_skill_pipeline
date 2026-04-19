from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from omni_skill_pipeline.exceptions import ProviderExecutionError, ProviderUnavailableError
from omni_skill_pipeline.providers.base import OCRBlock, OCRResult
from omni_skill_pipeline.utils import unique_preserve_order


class TesseractOCRProvider(object):
    def __init__(self, *, binary: str = 'tesseract', languages: str = 'eng+chi_sim') -> None:
        self.binary = binary
        self.languages = languages

    def extract(self, image_path: Path) -> OCRResult:
        executable = shutil.which(self.binary) or (self.binary if Path(self.binary).exists() else None)
        if not executable:
            raise ProviderUnavailableError('Tesseract binary not found: %s' % self.binary)

        languages_to_try = unique_preserve_order([self.languages, 'eng'])
        errors = []
        for language in languages_to_try:
            command = [
                executable,
                str(image_path),
                'stdout',
                '-l',
                language,
                '--psm',
                '6',
                '--oem',
                '1',
            ]
            try:
                process = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=15,
                )
            except subprocess.TimeoutExpired:
                errors.append('timeout(%s)' % language)
                continue

            if process.returncode != 0:
                errors.append('%s:%s' % (language, process.stderr.strip() or 'ocr failed'))
                continue

            lines = unique_preserve_order(line.strip() for line in process.stdout.splitlines() if line.strip())
            if not lines:
                errors.append('%s:empty' % language)
                continue
            return OCRResult(
                text='\n'.join(lines),
                blocks=[OCRBlock(text=line, confidence=0.75) for line in lines],
                engine='tesseract',
                metadata={'languages': language},
            )

        raise ProviderExecutionError('; '.join(errors) or 'Tesseract OCR failed.')
