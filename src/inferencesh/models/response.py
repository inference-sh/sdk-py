"""V3 API response envelope."""

from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class Response(Generic[T]):
    """Wraps the V3 API envelope — every API call returns this.

    Access .data for the DTO and .messages for any warnings the server surfaced.
    """

    __slots__ = ("data", "messages")

    def __init__(self, data: T, messages: Optional[List[Dict[str, Any]]] = None):
        self.data = data
        self.messages = messages or []

    @property
    def has_warnings(self) -> bool:
        return any(m.get("level") == "warning" for m in self.messages)

    def __repr__(self) -> str:
        msgs = f", messages={self.messages}" if self.messages else ""
        return f"Response(data={self.data!r}{msgs})"
