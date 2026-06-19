"""Omni Skill Pipeline package."""

from __future__ import annotations

from typing import Any

__all__ = ['DistillationService', 'build_service']
__version__ = '0.2.3'


def __getattr__(name: str) -> Any:
    if name == 'DistillationService':
        from omni_skill_pipeline.service import DistillationService

        return DistillationService
    if name == 'build_service':
        from omni_skill_pipeline.service import build_service

        return build_service
    raise AttributeError("module 'omni_skill_pipeline' has no attribute %r" % name)
