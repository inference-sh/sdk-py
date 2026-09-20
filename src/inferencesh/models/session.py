"""The session a stream function talks to.

An app declares a stream function by taking a ``session`` parameter after its
input::

    class App(BaseApp):
        async def stream(self, input_data: MyInput, session: Session) -> MyOutput:
            async for frame in session:          # bytes or str, in order
                await session.send(frame)        # bytes -> binary, str -> text,
                                                 # anything else -> JSON text
            return MyOutput(...)

The function runs until it returns; its return value is the result the
platform records. Frames from the client arrive in order; the iterator ends
(and ``recv()`` returns None) when the client closes. Returning ends the
stream for the client.

The object the kernel passes in implements this protocol; the class here is
for type hints and discovery.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional, Protocol, Union, runtime_checkable

Frame = Union[bytes, str]


@runtime_checkable
class Session(Protocol):
    """One live stream between a client and a stream function."""

    id: str
    metadata: Dict[str, Any]

    @property
    def closed(self) -> bool:
        """True once the client is gone or the app closed the session."""
        ...

    async def recv(self) -> Optional[Frame]:
        """Return the next frame from the client, or None once it is gone."""
        ...

    def __aiter__(self) -> AsyncIterator[Frame]:
        ...

    async def send(self, data: Any) -> None:
        """Send a frame: bytes as binary, str as text, anything else as JSON text."""
        ...

    async def close(self) -> None:
        """Stop reading from the client; the stream ends when the function returns."""
        ...
