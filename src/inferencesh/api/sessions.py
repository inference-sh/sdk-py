"""Sessions API - namespaced session operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..types import AppSession

if TYPE_CHECKING:
    from ..client import Inference, AsyncInference


class SessionHandle:
    """Handle for interacting with an active session.

    Example:
        ```python
        with client.session("my-app@abc123") as session:
            session.call("init", {"config": "..."})
            session.call("process", {"data": "..."})
        ```
    """

    def __init__(self, client: "Inference", app: str, session_id: str):
        self._client = client
        self._app = app
        self._session_id = session_id
        self._ended = False

    @property
    def session_id(self) -> str:
        """The session ID."""
        return self._session_id

    def call(
        self,
        function: str = "run",
        input: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make a call within this session.

        Args:
            function: Function name to call (default: "run")
            input: Input data for the function
            **kwargs: Additional parameters for run()

        Returns:
            The task result
        """
        if self._ended:
            raise RuntimeError("Session has been ended")

        return self._client.run(
            {
                "app": self._app,
                "function": function,
                "input": input or {},
                "session": self._session_id,
            },
            **kwargs,
        )

    def info(self) -> AppSession:
        """Get current session info."""
        return self._client.sessions.get(self._session_id)

    def keepalive(self) -> AppSession:
        """Extend session expiration."""
        return self._client.sessions.keepalive(self._session_id)

    def end(self) -> None:
        """End this session."""
        if not self._ended:
            self._client.sessions.end(self._session_id)
            self._ended = True

    def __enter__(self) -> "SessionHandle":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end()


class AsyncSessionHandle:
    """Async handle for interacting with an active session.

    Example:
        ```python
        async with client.session("my-app@abc123") as session:
            await session.call("init", {"config": "..."})
            await session.call("process", {"data": "..."})
        ```
    """

    def __init__(self, client: "AsyncInference", app: str, session_id: str):
        self._client = client
        self._app = app
        self._session_id = session_id
        self._ended = False

    @property
    def session_id(self) -> str:
        """The session ID."""
        return self._session_id

    async def call(
        self,
        function: str = "run",
        input: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make a call within this session.

        Args:
            function: Function name to call (default: "run")
            input: Input data for the function
            **kwargs: Additional parameters for run()

        Returns:
            The task result
        """
        if self._ended:
            raise RuntimeError("Session has been ended")

        return await self._client.run(
            {
                "app": self._app,
                "function": function,
                "input": input or {},
                "session": self._session_id,
            },
            **kwargs,
        )

    async def info(self) -> AppSession:
        """Get current session info."""
        return await self._client.sessions.get(self._session_id)

    async def keepalive(self) -> AppSession:
        """Extend session expiration."""
        return await self._client.sessions.keepalive(self._session_id)

    async def end(self) -> None:
        """End this session."""
        if not self._ended:
            await self._client.sessions.end(self._session_id)
            self._ended = True

    async def __aenter__(self) -> "AsyncSessionHandle":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.end()


class SessionsAPI:
    """Synchronous Sessions API.

    Example:
        ```python
        client = Inference(api_key="...")

        # Get session info
        info = client.sessions.get("sess_abc123")
        print(info["status"])

        # List sessions
        sessions = client.sessions.list()

        # Keep session alive
        client.sessions.keepalive("sess_abc123")

        # End session
        client.sessions.end("sess_abc123")
        ```
    """

    def __init__(self, client: "Inference") -> None:
        self._client = client

    def get(self, session_id: str) -> AppSession:
        """Get information about a session.

        Args:
            session_id: The session ID

        Returns:
            Session information

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        data = self._client._request("get", f"/sessions/{session_id}")
        return data

    def list(self) -> List[AppSession]:
        """List all sessions for the current user/team.

        Returns:
            List of session information
        """
        data = self._client._request("get", "/sessions")
        return data or []

    def keepalive(self, session_id: str) -> AppSession:
        """Extend session expiration time.

        Args:
            session_id: The session ID

        Returns:
            Updated session information

        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionExpiredError: If session has expired
            SessionEndedError: If session was ended
        """
        data = self._client._request("post", f"/sessions/{session_id}/keepalive")
        return data

    def end(self, session_id: str) -> None:
        """End a session and release the worker.

        Args:
            session_id: The session ID

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        self._client._request("delete", f"/sessions/{session_id}")


class AsyncSessionsAPI:
    """Asynchronous Sessions API.

    Example:
        ```python
        client = AsyncInference(api_key="...")

        # Get session info
        info = await client.sessions.get("sess_abc123")

        # List sessions
        sessions = await client.sessions.list()

        # Keep session alive
        await client.sessions.keepalive("sess_abc123")

        # End session
        await client.sessions.end("sess_abc123")
        ```
    """

    def __init__(self, client: "AsyncInference") -> None:
        self._client = client

    async def get(self, session_id: str) -> AppSession:
        """Get information about a session."""
        data = await self._client._request("get", f"/sessions/{session_id}")
        return data

    async def list(self) -> List[AppSession]:
        """List all sessions for the current user/team."""
        data = await self._client._request("get", "/sessions")
        return data or []

    async def keepalive(self, session_id: str) -> AppSession:
        """Extend session expiration time."""
        data = await self._client._request("post", f"/sessions/{session_id}/keepalive")
        return data

    async def end(self, session_id: str) -> None:
        """End a session and release the worker."""
        await self._client._request("delete", f"/sessions/{session_id}")
