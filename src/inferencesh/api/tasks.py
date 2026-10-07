"""Tasks API - namespaced task operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union, Iterator, TYPE_CHECKING

from ..models.response import Response

if TYPE_CHECKING:
    from ..client import Inference, AsyncInference, TaskStream, AsyncTaskStream


class TasksAPI:
    """Synchronous Tasks API.

    Example:
        ```python
        client = inference(api_key="...")

        # Run a task and wait for completion
        result = client.tasks.run({
            "app": "okaris/flux@abc1",
            "input": {"prompt": "hello"}
        })

        # Get task status
        task = client.tasks.get(task_id)

        # Stream task updates
        for update in client.tasks.stream(task_id):
            print(update)
        ```
    """

    def __init__(self, client: "Inference") -> None:
        self._client = client

    def run(
        self,
        params: Dict[str, Any],
        *,
        wait: bool = True,
        stream: bool = False,
        auto_reconnect: bool = True,
        max_reconnects: int = 5,
        reconnect_delay_ms: int = 1000,
    ) -> Union[Dict[str, Any], "TaskStream", Iterator[Dict[str, Any]]]:
        """Run a task with optional streaming updates.

        By default, this method waits for the task to complete and returns the final result.
        You can set wait=False to get just the task info, or stream=True to get an iterator
        of status updates.

        App Reference Format:
            ``namespace/name@shortid`` or ``namespace/name@shortid:function``

            The short ID ensures your code always runs the same version.
            You can optionally specify a function name to run a specific entry point.

        Args:
            params: Task parameters including:
                - app: App reference with version (e.g., "okaris/flux@abc1")
                - input: Input data for the app
                - setup: Optional setup parameters (affects worker warmth/scheduling)
            wait: Whether to wait for task completion (default: True)
            stream: Whether to return an iterator of updates (default: False)
            auto_reconnect: Whether to automatically reconnect on connection loss
            max_reconnects: Maximum number of reconnection attempts
            reconnect_delay_ms: Delay between reconnection attempts in milliseconds

        Returns:
            - If wait=True and stream=False: The completed task data
            - If wait=False: The created task info
            - If stream=True: An iterator of task updates
        """
        return self._client.run(
            params,
            wait=wait,
            stream=stream,
            auto_reconnect=auto_reconnect,
            max_reconnects=max_reconnects,
            reconnect_delay_ms=reconnect_delay_ms,
        )

    def get(self, task_id: str) -> Response[Any]:
        """Get the current state of a task.

        Args:
            task_id: The ID of the task to get

        Returns:
            Response wrapping the current task state
        """
        return self._client.get_task(task_id)

    def cancel(self, task_id: str) -> None:
        """Cancel a running task.

        Args:
            task_id: The ID of the task to cancel
        """
        self._client.cancel(task_id)

    def delete(self, task_id: str, *, files: bool = False) -> None:
        """Delete a finished task.

        Args:
            task_id: The ID of the task to delete
            files: Also delete the task's input and output files, even when
                something else still uses them
        """
        self._client._request("delete", f"/tasks/{task_id}", params={"files": "true"} if files else None)

    def files(self, task_id: str, *, role: Optional[str] = None) -> Any:
        """List the files a task consumed and produced.

        Args:
            task_id: The ID of the task
            role: "input" or "output" to list one side only

        Returns:
            Response wrapping a list of files, each with id, uri and role
        """
        return self._client._request("get", f"/tasks/{task_id}/files", params={"role": role} if role else None)

    def delete_files(self, task_id: str, *, role: Optional[str] = None) -> Any:
        """Delete a finished task's files and keep the task.

        A file is deleted even when something else still uses it.

        Args:
            task_id: The ID of the task
            role: "input" or "output" to delete one side only

        Returns:
            Response wrapping {"deleted": [...], "skipped": [...]}
        """
        return self._client._request("delete", f"/tasks/{task_id}/files", params={"role": role} if role else None)

    def stream(
        self,
        task_id: str,
        *,
        auto_reconnect: bool = True,
        max_reconnects: int = 5,
        reconnect_delay_ms: int = 1000,
    ) -> "TaskStream":
        """Create a TaskStream for getting streaming updates from a task.

        Args:
            task_id: The ID of the task to stream
            auto_reconnect: Whether to automatically reconnect on connection loss
            max_reconnects: Maximum number of reconnection attempts
            reconnect_delay_ms: Delay between reconnection attempts in milliseconds

        Returns:
            A stream interface for the task
        """
        return self._client.stream_task(
            task_id,
            auto_reconnect=auto_reconnect,
            max_reconnects=max_reconnects,
            reconnect_delay_ms=reconnect_delay_ms,
        )

    def wait_for_completion(self, task_id: str) -> Dict[str, Any]:
        """Wait for a task to complete and return its final state.

        Args:
            task_id: The ID of the task to wait for

        Returns:
            The final task state
        """
        return self._client.wait_for_completion(task_id)


class AsyncTasksAPI:
    """Asynchronous Tasks API.

    Example:
        ```python
        client = async_inference(api_key="...")

        # Run a task and wait for completion
        result = await client.tasks.run({
            "app": "okaris/flux@abc1",
            "input": {"prompt": "hello"}
        })

        # Get task status
        task = await client.tasks.get(task_id)

        # Stream task updates
        async for update in client.tasks.stream(task_id):
            print(update)
        ```
    """

    def __init__(self, client: "AsyncInference") -> None:
        self._client = client

    async def run(
        self,
        params: Dict[str, Any],
        *,
        wait: bool = True,
        stream: bool = False,
        auto_reconnect: bool = True,
        max_reconnects: int = 5,
        reconnect_delay_ms: int = 1000,
    ) -> Union[Dict[str, Any], "AsyncTaskStream"]:
        """Run a task with optional streaming updates.

        See TasksAPI.run for full documentation.
        """
        return await self._client.run(
            params,
            wait=wait,
            stream=stream,
            auto_reconnect=auto_reconnect,
            max_reconnects=max_reconnects,
            reconnect_delay_ms=reconnect_delay_ms,
        )

    async def get(self, task_id: str) -> Response[Any]:
        """Get the current state of a task."""
        return await self._client.get_task(task_id)

    async def cancel(self, task_id: str) -> None:
        """Cancel a running task."""
        await self._client.cancel(task_id)

    async def delete(self, task_id: str, *, files: bool = False) -> None:
        """Delete a finished task. With files=True its input and output files go too."""
        await self._client._request("delete", f"/tasks/{task_id}", params={"files": "true"} if files else None)

    async def files(self, task_id: str, *, role: Optional[str] = None) -> Any:
        """List the files a task consumed and produced."""
        return await self._client._request("get", f"/tasks/{task_id}/files", params={"role": role} if role else None)

    async def delete_files(self, task_id: str, *, role: Optional[str] = None) -> Any:
        """Delete a finished task's files and keep the task."""
        return await self._client._request("delete", f"/tasks/{task_id}/files", params={"role": role} if role else None)

    def stream(
        self,
        task_id: str,
        *,
        auto_reconnect: bool = True,
        max_reconnects: int = 5,
        reconnect_delay_ms: int = 1000,
    ) -> "AsyncTaskStream":
        """Create an AsyncTaskStream for getting streaming updates from a task."""
        return self._client.stream_task(
            task_id,
            auto_reconnect=auto_reconnect,
            max_reconnects=max_reconnects,
            reconnect_delay_ms=reconnect_delay_ms,
        )

    async def wait_for_completion(self, task_id: str) -> Dict[str, Any]:
        """Wait for a task to complete and return its final state."""
        return await self._client.wait_for_completion(task_id)
