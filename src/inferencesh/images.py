"""Fit an image to what a model provider accepts, by downsizing only.

Model apps send images from local files (an input, a tool result, an image
earlier in the conversation). A provider downscales an image above its native
resolution anyway, and refuses one above its hard limits (bytes, format), so
an app fits each image to its provider before sending it:

    data, mime = fit_image(file.path, ImageLimits(max_long_edge=2576, max_pixels=3_750_000))

An image is never upscaled and never re-encoded when it already fits. It is
scaled down when it exceeds max_long_edge or max_pixels, re-encoded when its
format is not one the provider takes, and re-encoded at lower quality (then
smaller) when it still exceeds max_bytes.

Needs Pillow (pip install "inferencesh[images]"). Without it the original
bytes are returned unchanged.
"""

import io
import logging
import math
import mimetypes
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_FORMAT_MIME = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "GIF": "image/gif",
    "WEBP": "image/webp",
}
_MIME_FORMAT = {mime: fmt for fmt, mime in _FORMAT_MIME.items()}


@dataclass(frozen=True)
class ImageLimits:
    """What a provider takes. None means no limit of that kind."""

    max_long_edge: Optional[int] = None
    max_pixels: Optional[int] = None
    max_bytes: Optional[int] = None
    mime_types: Tuple[str, ...] = ("image/png", "image/jpeg", "image/gif", "image/webp")


def _sniff_mime(data: bytes, path: str) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return mimetypes.guess_type(path)[0] or "application/octet-stream"


def _scale(width: int, height: int, limits: ImageLimits) -> float:
    scale = 1.0
    if limits.max_long_edge and max(width, height) > limits.max_long_edge:
        scale = min(scale, limits.max_long_edge / max(width, height))
    if limits.max_pixels and width * height > limits.max_pixels:
        scale = min(scale, math.sqrt(limits.max_pixels / (width * height)))
    return scale


def fit_image(path: str, limits: ImageLimits) -> Tuple[bytes, str]:
    """The image at path as (bytes, mime type), fitted to limits by downsizing only."""
    with open(path, "rb") as f:
        data = f.read()
    mime = _sniff_mime(data, path)

    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow is not installed; sending %s unfitted (pip install 'inferencesh[images]')", path)
        return data, mime

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:  # not an image Pillow reads: send as is
        logger.warning("could not read %s as an image (%s); sending unfitted", path, exc)
        return data, mime

    scale = _scale(img.width, img.height, limits)
    fits_format = mime in limits.mime_types
    fits_bytes = limits.max_bytes is None or len(data) <= limits.max_bytes
    if scale >= 1.0 and fits_format and fits_bytes:
        return data, mime

    if getattr(img, "is_animated", False):
        img.seek(0)  # providers read only the first frame
    if scale < 1.0:
        size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        img = img.resize(size, Image.LANCZOS)

    out_mime = mime if fits_format else ("image/png" if "image/png" in limits.mime_types else limits.mime_types[0])
    encoded = _encode(img, out_mime)

    # Still over the byte limit: lossy JPEG (or WebP) at falling quality, then smaller.
    if limits.max_bytes is not None and len(encoded) > limits.max_bytes:
        lossy = next((m for m in ("image/jpeg", "image/webp") if m in limits.mime_types), None)
        if lossy is not None:
            out_mime = lossy
            for quality in (90, 80, 70):
                encoded = _encode(img, lossy, quality)
                if len(encoded) <= limits.max_bytes:
                    break
            while len(encoded) > limits.max_bytes and min(img.size) > 64:
                img = img.resize((max(1, int(img.width * 0.75)), max(1, int(img.height * 0.75))), Image.LANCZOS)
                encoded = _encode(img, lossy, 70)
    return encoded, out_mime


def _encode(img, mime: str, quality: int = 90) -> bytes:
    fmt = _MIME_FORMAT[mime]
    if fmt == "JPEG" and img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif fmt in ("PNG", "WEBP") and img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
        img = img.convert("RGBA")
    buf = io.BytesIO()
    kwargs = {"quality": quality} if fmt in ("JPEG", "WEBP") else {}
    img.save(buf, format=fmt, **kwargs)
    return buf.getvalue()
