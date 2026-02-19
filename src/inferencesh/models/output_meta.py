"""Output metadata types for pricing and usage tracking.

Types and field names are kept in sync with Go source of truth
(common-go/pkg/models/usage.go) via generated output_meta_gen.py.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field

# Import generated enums from Go source of truth
from inferencesh.output_meta_gen import MetaItemType, VideoResolution


class MetaItem(BaseModel):
    """Base class for input/output metadata items."""
    type: str  # "text", "image", "video", "audio", "raw"
    extra: Optional[dict[str, Any]] = Field(
        default=None,
        description="App-specific key-value pairs for custom pricing factors"
    )


class TextMeta(MetaItem):
    """Metadata for text inputs/outputs (e.g., LLM tokens)."""
    type: str = MetaItemType.TEXT.value
    tokens: int = Field(
        default=0,
        description="Token count - in inputs[] = input tokens, in outputs[] = output tokens"
    )


class ImageMeta(MetaItem):
    """Metadata for image inputs/outputs."""
    type: str = MetaItemType.IMAGE.value
    width: int = Field(default=0, description="Image width in pixels")
    height: int = Field(default=0, description="Image height in pixels")
    resolution_mp: float = Field(
        default=0,
        description="Resolution in megapixels (width * height / 1_000_000)"
    )
    steps: int = Field(default=0, description="Number of diffusion steps")
    count: int = Field(default=1, description="Number of images")


class VideoMeta(MetaItem):
    """Metadata for video inputs/outputs."""
    type: str = MetaItemType.VIDEO.value
    width: int = Field(default=0, description="Video width in pixels")
    height: int = Field(default=0, description="Video height in pixels")
    resolution_mp: float = Field(
        default=0,
        description="Resolution in megapixels per frame"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Standard resolution preset (480p, 720p, 1080p, 1440p, 4k)"
    )
    seconds: float = Field(default=0, description="Duration in seconds")
    fps: int = Field(default=0, description="Frames per second")


class AudioMeta(MetaItem):
    """Metadata for audio inputs/outputs."""
    type: str = MetaItemType.AUDIO.value
    seconds: float = Field(default=0, description="Duration in seconds")
    sample_rate: int = Field(default=0, description="Sample rate in Hz")


class RawMeta(MetaItem):
    """Metadata for raw inputs/outputs used for custom pricing."""
    type: str = MetaItemType.RAW.value
    cost: float = Field(default=0, description="Cost in dollar cents")


# Union type for proper serialization of all MetaItem subclasses
MetaItemUnion = TextMeta | ImageMeta | VideoMeta | AudioMeta | RawMeta


class OutputMeta(BaseModel):
    """
    Structured metadata about task inputs and outputs for pricing calculation.

    Apps include this in their output to report what was consumed (inputs)
    and what was produced (outputs). The backend uses this with CEL expressions
    to calculate app-level pricing.

    Example usage in an LLM app:
        output_meta = OutputMeta(
            inputs=[TextMeta(tokens=150)],
            outputs=[TextMeta(tokens=500)]
        )

    Example usage in a video generation app:
        output_meta = OutputMeta(
            outputs=[VideoMeta(
                resolution="1080p",
                resolution_mp=2.07,
                seconds=10.5,
                fps=30
            )]
        )
    """
    inputs: List[MetaItemUnion] = Field(
        default_factory=list,
        description="Metadata about consumed inputs"
    )
    outputs: List[MetaItemUnion] = Field(
        default_factory=list,
        description="Metadata about produced outputs"
    )
