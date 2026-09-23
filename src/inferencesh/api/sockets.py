"""Sockets API: the duplex connection of a stream task.

A stream function keeps a socket open with its caller for the life of the
task. The run response carries the caller's end (``task["socket"]``);
``AsyncSocketsAPI.open`` dials it and gives back an AsyncLiveSession.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from ..types import CursorListRequest, CursorListResponse, FilterOperator, SocketAccess, SocketDTO, TaskStatus
from ..live import AsyncLiveSession, OnBinary, OnPatch, OnState, WsConnect

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

    async def open(
        self,
        target: SocketTarget,
        *,
        watch_task: bool = True,
        on_state: Optional[OnState] = None,
        on_binary: Optional[OnBinary] = None,
        on_patch: Optional[OnPatch] = None,
        ws_connect: Optional[WsConnect] = None,
        poll_interval: float = 2.0,
    ) -> AsyncLiveSession:
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
            on_state, on_binary, on_patch: Session callbacks.
            ws_connect: ``async (url) -> ws`` to dial with (tests, another transport).
            poll_interval: Seconds between task status polls while waiting.
        """
        task: Dict[str, Any] = (await self._client.get_task(target)).data if isinstance(target, str) else target
        task_id = task["id"]
        access: Optional[SocketAccess] = None if isinstance(target, str) else task.get("socket")
        socket_id = access["id"] if access else None
        if access is None:
            socket = await self.for_task(task_id)
            if socket is None:
                raise ValueError(f"task {task_id} has no socket: is it a stream function?")
            socket_id = socket["id"]
            access = await self.access(socket_id)

        async def renew() -> SocketAccess:
            return await self.access(socket_id)  # type: ignore[arg-type]

        session = AsyncLiveSession(
            access,
            renew=renew,
            task_watch=_watch_task_status(self._client, task_id, poll_interval) if watch_task else None,
            on_state=on_state,
            on_binary=on_binary,
            on_patch=on_patch,
            ws_connect=ws_connect,
        )
        await session.connect()
        return session


async def _watch_task_status(client: "AsyncInference", task_id: str, poll_interval: float) -> Dict[str, Any]:
    """Polls ``GET /tasks/{id}/status`` until the task ends. Returns the status
    on completion; raises RuntimeError when it failed or was cancelled."""
    from ..client import parse_status

    while True:
        status_dto = (await client._request("get", f"/tasks/{task_id}/status")).data or {}
        status = parse_status(status_dto.get("status"))
        if status == TaskStatus.COMPLETED:
            return status_dto
        if status == TaskStatus.FAILED:
            raise RuntimeError(await _task_error(client, task_id) or "task failed")
        if status == TaskStatus.CANCELLED:
            raise RuntimeError("task cancelled")
        await asyncio.sleep(poll_interval)


async def _task_error(client: "AsyncInference", task_id: str) -> Optional[str]:
    """The status endpoint carries no error; the task does."""
    try:
        return ((await client.get_task(task_id)).data or {}).get("error")
    except Exception:
        return None


__all__ = ["SocketsAPI", "AsyncSocketsAPI", "SocketTarget"]
