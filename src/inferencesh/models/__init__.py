"""Models package for inference.sh SDK."""

from .base import BaseApp, BaseAppInput, BaseAppOutput, BaseAppSetup, Metadata
from .file import File
from .llm import (
    ContextMessageRole,
    Message,
    ContextMessage,
    LLMInput,
    LLMOutput,
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
)
from inferencesh.output_meta_gen import MetaItemType, VideoResolution
from .errors import (
    APIError,
    RequirementsNotMetError,
    RequirementError,
    SetupAction,
)

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
    "LLMInput",
    "LLMOutput",
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
    # Error types
    "APIError",
    "RequirementsNotMetError",
    "RequirementError",
    "SetupAction",
]
