"""StreamDelta — marker base class for all streaming delta types.

The engine checks ``isinstance(output, StreamDelta)`` once to route yields
to the delta channel instead of the progress channel. Subclasses carry the
actual payload shape (LLMDelta, ChatCompletionChunk, ImageProgressDelta, etc.)
without requiring engine changes per type.
"""

from pydantic import BaseModel


class StreamDelta(BaseModel):
    pass
