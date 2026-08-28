"""Models package for inference.sh SDK."""

from .base import BaseApp, BaseAppInput, BaseAppOutput, BaseAppSetup, Metadata
from .file import File
from .llm import (
    ContextMessageRole,
    Message,
    ContextMessage,
    ChatInput,
    LLMInput,
    LLMOutput,
    LLMDelta,
    ModelSettings,
    ModelSettingsCapabilityMixin,
    build_messages,
    stream_generate,
    timing_context,
)
from .output_meta import (
    MetaItem,
    TextMeta,
    ImageMeta,
    VideoMeta,
    AudioMeta,
    RawMeta,
    OutputMeta,
    probe_video,
)
from inferencesh.output_meta_gen import MetaItemType, VideoResolution
from .errors import (
    APIError,
    RequirementsNotMetError,
    RequirementError,
    SetupAction,
)
from .response import Response

__all__ = [
    "BaseApp",
    "BaseAppInput",
    "BaseAppOutput",
    "BaseAppSetup",
    "File",
    "Metadata",
    # LLM types
    "ContextMessageRole",
    "Message",
    "ContextMessage",
    "ChatInput",
    "LLMInput",
    "LLMOutput",
    "LLMDelta",
    "ModelSettings",
    "ModelSettingsCapabilityMixin",
    "build_messages",
    "stream_generate",
    "timing_context",
    # OutputMeta types
    "MetaItem",
    "MetaItemType",
    "TextMeta",
    "ImageMeta",
    "VideoMeta",
    "VideoResolution",
    "AudioMeta",
    "RawMeta",
    "OutputMeta",
    "probe_video",
    # Error types
    "APIError",
    "RequirementsNotMetError",
    "RequirementError",
    "SetupAction",
    # Response envelope
    "Response",
]
