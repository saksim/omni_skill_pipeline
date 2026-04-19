from __future__ import annotations


class OmniSkillPipelineError(Exception):
    """Base error for pipeline failures."""


class ProviderUnavailableError(OmniSkillPipelineError):
    """Raised when a provider is not configured or not installed."""


class ProviderExecutionError(OmniSkillPipelineError):
    """Raised when an external provider fails while processing a request."""


class MediaProcessingError(OmniSkillPipelineError):
    """Raised when media extraction fails."""
