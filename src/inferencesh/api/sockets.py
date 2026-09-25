"""Sockets API: the duplex connection of a stream task.

A stream function keeps a socket open with its caller for the life of the
task. The run response carries the caller's end (``task["socket"]``);
``AsyncSocketsAPI.open`` dials it and gives back an AsyncLiveSession.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from ..types import CursorListRequest, CursorListResponse, FilterOperator, SocketAccess, SocketDTO, TaskStatus
from ..live import AsyncLiveSession

if TYPE_CHECKING:
    from ..client import Inference, AsyncInference

# The run response, a task, or a task id.
SocketTarget = Union[Dict[str, Any], str]


def _task_filter(task_id: str) -> CursorListRequest:
    return {"limit": 1, "filters": [{"field": "task_id", "operator": FilterOperator.OP_EQUAL, "value": task_id}]}


class SocketsAPI:
    """Synchronous Sockets API: the HTTP side only. Dialling a socket is
    async; see ``AsyncInference.live`` / ``AsyncSocketsAPI.open``."""

    def __init__(self, client: "Inference") -> None:
        self._client = client

    def get(self, socket_id: str) -> SocketDTO:
        return self._client._request("get", f"/sockets/{socket_id}").data

    def list(self, params: Optional[CursorListRequest] = None) -> CursorListResponse:
        return self._client._request("post", "/sockets/list", data=dict(params or {})).data

    def for_task(self, task_id: str) -> Optional[SocketDTO]:
        """The task's socket, or None when it has none (not a stream function)."""
        items = (self.list(_task_filter(task_id)) or {}).get("items") or []
        return items[0] if items else None

    def access(self, socket_id: str) -> SocketAccess:
        """A fresh credential for the caller's end, e.g. after a restart or to redial."""
        return self._client._request("post", f"/sockets/{socket_id}/access").data

    def delete(self, socket_id: str) -> None:
        self._client._request("delete", f"/sockets/{socket_id}")

    def open(self, target: SocketTarget, **kwargs: Any) -> None:
        raise NotImplementedError(
            "a live socket needs the async client: use AsyncInference (pip install inferencesh[async]) "
            "and `await client.sockets.open(...)` or `await client.live(...)`"
        )


class AsyncSocketsAPI:
    """Asynchronous Sockets API.

    Example:
        ```python
        client = AsyncInference(api_key="...")
        task = await client.run({"app": "infsh/voice-loop", "function": "stream", "input": {}}, wait=False)
        session = await client.sockets.open(task)
        async for frame in session:
            ...
        ```
    """

    def __init__(self, client: "AsyncInference") -> None:
        self._client = client

    async def get(self, socket_id: str) -> SocketDTO:
        return (await self._client._request("get", f"/sockets/{socket_id}")).data

    async def list(self, params: Optional[CursorListRequest] = None) -> CursorListResponse:
        return (await self._client._request("post", "/sockets/list", data=dict(params or {}))).data

    async def for_task(self, task_id: str) -> Optional[SocketDTO]:
        """The task's socket, or None when it has none (not a stream function)."""
        items = ((await self.list(_task_filter(task_id))) or {}).get("items") or []
        return items[0] if items else None

    async def access(self, socket_id: str) -> SocketAccess:
        """A fresh credential for the caller's end, e.g. after a restart or to redial."""
        return (await self._client._request("post", f"/sockets/{socket_id}/access")).data

    async def delete(self, socket_id: str) -> None:
        await self._client._request("delete", f"/sockets/{socket_id}")

    async def open(self, target: SocketTarget, *, watch_task: bool = True, **session_options: Any) -> AsyncLiveSession:
        """Dials the caller's end of a stream task's socket. Returns once the
        relay accepted the connection: the session is ``waiting`` until the
        app's first frame, then ``live``; see AsyncLiveSession.

        Args:
            target: The run response (which carries the access), a task dict,
                or a task id. Without an access in hand the task's socket is
                looked up and a credential issued for it.
            watch_task: Follow the task while waiting for the app, and end the
                session if the task ends first (default: True). Off, a task
                that fails before its worker dials leaves the session waiting
                until the relay's pair timeout.
            **session_options: Passed to AsyncLiveSession: the callbacks
                (``on_state``, ``on_binary``, ``on_patch``, ``on_text``,
                ``on_update``, ``on_clear``, ``on_error``), ``input_schema`` /
                ``output_schema`` to map frames to fields, and ``ws_connect``.
        """
        task_id: str = target if isinstance(target, str) else target["id"]
        access: Optional[SocketAccess] = None if isinstance(target, str) else target.get("socket")
        if access is None:
            socket = await self.for_task(task_id)
            if socket is None:
                raise ValueError(f"task {task_id} has no socket: is it a stream function?")
            access = await self.access(socket["id"])
        socket_id = access["id"]

        async def renew() -> SocketAccess:
            return await self.access(socket_id)

        session = AsyncLiveSession(
            access,
            renew=renew,
            # The same watch the client waits on tasks with (SSE, reconciled by GET).
            task_watch=self._client.wait_for_completion(task_id) if watch_task else None,
            **session_options,
        )
        await session.connect()
        return session


__all__ = ["SocketsAPI", "AsyncSocketsAPI", "SocketTarget"]
