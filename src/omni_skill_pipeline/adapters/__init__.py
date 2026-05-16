from __future__ import annotations

from typing import Any

__all__ = ['AudioAdapter', 'ImageAdapter', 'TabularAdapter', 'TextAdapter', 'VideoAdapter']


def __getattr__(name: str) -> Any:
    if name == 'AudioAdapter':
        from omni_skill_pipeline.adapters.audio import AudioAdapter

        return AudioAdapter
    if name == 'ImageAdapter':
        from omni_skill_pipeline.adapters.image import ImageAdapter

        return ImageAdapter
    if name == 'TabularAdapter':
        from omni_skill_pipeline.adapters.tabular import TabularAdapter

        return TabularAdapter
    if name == 'TextAdapter':
        from omni_skill_pipeline.adapters.text import TextAdapter

        return TextAdapter
    if name == 'VideoAdapter':
        from omni_skill_pipeline.adapters.video import VideoAdapter

        return VideoAdapter
    raise AttributeError("module 'omni_skill_pipeline.adapters' has no attribute %r" % name)
