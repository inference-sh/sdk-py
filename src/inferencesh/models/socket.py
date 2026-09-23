"""The socket a stream function talks to.

An app declares a stream function by taking a ``socket`` parameter after its
input (``sock`` also works, for functions that use the stdlib socket module)::

    class App(BaseApp):
        async def stream(self, input_data: MyInput, socket: Socket) -> MyOutput:
            async for frame in socket:           # bytes or str, in order
                await socket.send(frame)         # bytes -> binary, str -> text,
                                                 # anything else -> JSON text
            return MyOutput(...)

The function runs until it returns; its return value is the result the
platform records. Frames from the client arrive in order; the iterator ends
(and ``recv()`` returns None) when the client closes. Returning ends the
stream for the client. This is a different thing from the platform's app
session (a worker leased across several calls): a stream function runs as one
call, inside an app session or on its own.

The object the kernel passes in implements this protocol; the class here is
for type hints.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional, Protocol, Union, runtime_checkable

Frame = Union[bytes, str]


@runtime_checkable
class Socket(Protocol):
    """One live stream between a client and a stream function."""

    id: str
    metadata: Dict[str, Any]

    dropped: int
    """How many binary frames the kernel has dropped because the app read too slowly."""

    binary_backlog: Optional[int]
    """The most binary frames kept queued (256); None keeps every one of them."""

    @property
    def closed(self) -> bool:
        """True once the client is gone or the app closed the socket."""
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
