from __future__ import annotations

import logging
from typing import Dict

from omni_skill_pipeline.interfaces import ArtifactRepository
from omni_skill_pipeline.models import DistillBundle

logger = logging.getLogger(__name__)


class DualWriteArtifactRepository(ArtifactRepository):
    """Write to primary repository first, then mirror to secondary repository."""

    def __init__(
        self,
        primary: ArtifactRepository,
        secondary: ArtifactRepository,
        *,
        continue_on_secondary_error: bool = True,
        secondary_prefix: str = 'secondary_',
    ) -> None:
        if not secondary_prefix.strip():
            raise ValueError('secondary_prefix cannot be empty.')
        self.primary = primary
        self.secondary = secondary
        self.continue_on_secondary_error = continue_on_secondary_error
        self.secondary_prefix = secondary_prefix

    def save_bundle(self, bundle: DistillBundle) -> Dict[str, str]:
        primary_artifacts = self.primary.save_bundle(bundle)

        secondary_artifacts: Dict[str, str] = {}
        secondary_error: Exception | None = None
        try:
            secondary_artifacts = self.secondary.save_bundle(bundle)
        except Exception as exc:
            if not self.continue_on_secondary_error:
                raise
            secondary_error = exc
            logger.warning(
                'Dual-write secondary repository failed; keep primary artifacts.',
                exc_info=exc,
            )

        merged = dict(primary_artifacts)
        for key, value in secondary_artifacts.items():
            merged['%s%s' % (self.secondary_prefix, key)] = value
        if secondary_error is not None:
            merged['%serror' % self.secondary_prefix] = str(secondary_error)

        bundle.artifacts = merged
        return merged
