"""Tasks API - namespaced task operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union, Iterator, AsyncIterator, TYPE_CHECKING

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
                - variant: Optional variant name
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

    def get(self, task_id: str) -> Dict[str, Any]:
        """Get the current state of a task.

        Args:
            task_id: The ID of the task to get

        Returns:
            The current task state
        """
        return self._client.get_task(task_id)

    def cancel(self, task_id: str) -> None:
        """Cancel a running task.

        Args:
            task_id: The ID of the task to cancel
        """
        self._client.cancel(task_id)

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

    async def get(self, task_id: str) -> Dict[str, Any]:
        """Get the current state of a task."""
        return await self._client.get_task(task_id)

    async def cancel(self, task_id: str) -> None:
        """Cancel a running task."""
        await self._client.cancel(task_id)

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
