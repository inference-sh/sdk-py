"""Unit tests for Sessions API and SessionHandle (mocked HTTP)."""

import json
from unittest.mock import MagicMock

import pytest

from inferencesh import Inference, AsyncInference, TaskStatus
from inferencesh.api.sessions import SessionHandle


@pytest.fixture
def patch_sessions_requests(monkeypatch):
    """Mock requests for session CRUD and task runs."""
    calls = []

    def fake_request(method, url, params=None, data=None, headers=None, stream=False, timeout=None):
        calls.append({
            "method": method.upper(),
            "url": url,
            "data": json.loads(data) if data else None,
        })

        if url.endswith("/apps/run") and method.upper() == "POST":
            body = calls[-1]["data"]
            return _dummy_response(json_data={
                "id": "task_sess",
                "status": 1,
                "session_id": "sess_new",
                "input": body.get("input"),
            })

        if "/tasks/task_sess" in url and method.upper() == "GET" and not url.endswith("/stream"):
            return _dummy_response(json_data={
                "id": "task_sess",
                "status": 10,
                "session_id": "sess_new",
                "output": {"ok": True},
            })

        if url.endswith("/tasks/task_sess/stream") and stream:
            event = json.dumps({
                "id": "task_sess",
                "status": 10,
                "session_id": "sess_new",
                "output": {"ok": True},
            })
            return _StreamResponse(lines=[event])

        if url.endswith("/sessions/sess_new") and method.upper() == "GET":
            return _dummy_response(json_data={"id": "sess_new", "status": "active"})

        if url.endswith("/sessions/sess_new/keepalive") and method.upper() == "POST":
            return _dummy_response(json_data={"id": "sess_new", "status": "active", "expires_at": "2099-01-01"})

        if url.endswith("/sessions/sess_new") and method.upper() == "DELETE":
            return _dummy_response(status_code=204, json_data=None)

        if url.endswith("/sessions") and method.upper() == "GET":
            return _dummy_response(json_data=[{"id": "sess_new", "status": "active"}])

        return _dummy_response(status_code=404, json_data={"detail": "not found"})

    class FakeRequestsModule:
        def request(self, *args, **kwargs):
            return fake_request(*args, **kwargs)

    import inferencesh.client as client_mod

    monkeypatch.setattr(client_mod, "_require_requests", lambda: FakeRequestsModule())

    yield calls


class _dummy_response:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = json.dumps(self._json_data) if self._json_data is not None else ""

    @property
    def ok(self):
        return 200 <= self.status_code < 300


class _StreamResponse:
    def __init__(self, lines):
        self.status_code = 200
        self._lines = lines
        self.raw = None

    @property
    def ok(self):
        return True

    def iter_lines(self, decode_unicode=False, chunk_size=None):
        for line in self._lines:
            yield line

    def close(self):
        pass


def test_session_context_manager_runs_and_ends(patch_sessions_requests):
    client = Inference(api_key="test")

    with client.session("my-app@v1", input={"start": True}) as session:
        assert session.session_id == "sess_new"
        session.call("step", {"x": 1}, wait=False)

    run_calls = [c for c in patch_sessions_requests if c["url"].endswith("/apps/run")]
    assert len(run_calls) == 2
    assert run_calls[0]["data"]["session"] == "new"
    assert run_calls[1]["data"]["session"] == "sess_new"
    assert run_calls[1]["data"]["function"] == "step"

    delete_calls = [c for c in patch_sessions_requests if c["method"] == "DELETE"]
    assert len(delete_calls) == 1


def test_session_call_wait_returns_completed_output(patch_sessions_requests):
    """session.call() defaults to wait=True and returns the completed task dict."""
    client = Inference(api_key="test")

    with client.session("my-app@v1", input={"start": True}) as session:
        result = session.call("step", {"x": 1})

    assert result["session_id"] == "sess_new"
    assert result["output"] == {"ok": True}
    assert result["status"] == TaskStatus.COMPLETED


def test_session_call_stream_yields_updates(patch_sessions_requests):
    """session.call(stream=True) matches client.run() streaming semantics."""
    client = Inference(api_key="test")

    with client.session("my-app@v1") as session:
        updates = []
        for update in session.call("step", {"x": 1}, stream=True):
            updates.append(update)
            if update.get("status") == TaskStatus.COMPLETED:
                break

    assert len(updates) >= 1
    assert updates[-1]["output"] == {"ok": True}


def test_session_creation_without_session_id_raises(monkeypatch):
    """client.session() requires a dict with session_id from the initial run."""
    client = Inference(api_key="test")
    monkeypatch.setattr(
        client,
        "run",
        lambda *args, **kwargs: {"id": "task_no_sess", "status": 1},
    )

    with pytest.raises(RuntimeError, match="no session_id returned"):
        with client.session("my-app@v1"):
            pass


def test_session_call_after_end_raises(patch_sessions_requests):
    client = Inference(api_key="test")
    handle = SessionHandle(client, "my-app@v1", "sess_new")
    handle.end()

    with pytest.raises(RuntimeError, match="Session has been ended"):
        handle.call("step")


def test_session_handle_info_and_keepalive(patch_sessions_requests):
    """SessionHandle.info/keepalive delegate to the sessions namespace."""
    client = Inference(api_key="test")
    handle = SessionHandle(client, "my-app@v1", "sess_new")

    info = handle.info()
    assert info["id"] == "sess_new"

    kept = handle.keepalive()
    assert kept["expires_at"] == "2099-01-01"

    get_calls = [c for c in patch_sessions_requests if c["url"].endswith("/sessions/sess_new") and c["method"] == "GET"]
    keepalive_calls = [c for c in patch_sessions_requests if c["url"].endswith("/keepalive")]
    assert len(get_calls) == 1
    assert len(keepalive_calls) == 1


def test_sessions_api_get_list_keepalive_end(patch_sessions_requests):
    client = Inference(api_key="test")

    info = client.sessions.get("sess_new")
    assert info["id"] == "sess_new"

    sessions = client.sessions.list()
    assert len(sessions) == 1

    kept = client.sessions.keepalive("sess_new")
    assert kept["expires_at"] == "2099-01-01"

    client.sessions.end("sess_new")
    assert any(c["method"] == "DELETE" for c in patch_sessions_requests)


def test_sessions_api_unwraps_v3_envelope(monkeypatch):
    """Sessions CRUD must read .data from V3 {data, messages} responses."""
    import inferencesh.client as client_mod

    session_dto = {"id": "sess_v3", "status": "active"}
    envelope = {
        "data": session_dto,
        "messages": [{"level": "warning", "message": "session expiring soon"}],
    }

    def fake_request(method, url, params=None, data=None, headers=None, stream=False, timeout=None):
        if url.endswith("/sessions/sess_v3") and method.upper() == "GET":
            return _dummy_response(json_data=envelope)
        if url.endswith("/sessions") and method.upper() == "GET":
            return _dummy_response(json_data={"data": [session_dto], "messages": []})
        if url.endswith("/sessions/sess_v3/keepalive") and method.upper() == "POST":
            return _dummy_response(json_data={
                "data": {**session_dto, "expires_at": "2099-12-31"},
                "messages": [],
            })
        return _dummy_response(status_code=404, json_data={"detail": "not found"})

    class FakeRequestsModule:
        def request(self, *args, **kwargs):
            return fake_request(*args, **kwargs)

    monkeypatch.setattr(client_mod, "_require_requests", lambda: FakeRequestsModule())

    client = Inference(api_key="test")
    assert client.sessions.get("sess_v3") == session_dto
    assert client.sessions.list() == [session_dto]
    assert client.sessions.keepalive("sess_v3")["expires_at"] == "2099-12-31"


@pytest.mark.asyncio
async def test_async_sessions_api(monkeypatch):
    """Async sessions namespace hits _request with expected paths."""
    calls = []

    class MockAsyncResponse:
        def __init__(self, json_data=None, status=200):
            self._json_data = json_data if json_data is not None else {"id": "sess_a"}
            self.status = status
            self.content_type = "application/json"

        @property
        def ok(self):
            return self.status < 400

        async def text(self):
            return json.dumps(self._json_data)

        async def json(self):
            return self._json_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def request(self, method, url, **kwargs):
            calls.append({"method": method.upper(), "url": url})
            if url.endswith("/sessions") and method.upper() == "GET":
                return MockAsyncResponse([{"id": "sess_a"}])
            if method.upper() == "DELETE":
                return MockAsyncResponse(status=204)
            return MockAsyncResponse({"id": "sess_a"})

    mock_aiohttp = MagicMock()
    mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
    mock_aiohttp.ClientSession = lambda **kwargs: MockClientSession()

    import inferencesh.client as client_mod

    async def require_aiohttp():
        return mock_aiohttp

    monkeypatch.setattr(client_mod, "_require_aiohttp", require_aiohttp)

    client = AsyncInference(api_key="test")
    info = await client.sessions.get("sess_a")
    assert info["id"] == "sess_a"

    listed = await client.sessions.list()
    assert listed[0]["id"] == "sess_a"

    await client.sessions.end("sess_a")
    assert any(c["method"] == "DELETE" for c in calls)


@pytest.mark.asyncio
async def test_async_session_context_manager(monkeypatch):
    """Async session context manager creates session and forwards call() to run()."""
    calls = []

    class _AsyncStreamIter:
        def __init__(self, lines):
            self._lines = iter(lines)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self._lines)
            except StopIteration:
                raise StopAsyncIteration from None

    class MockAsyncResponse:
        def __init__(self, json_data=None, status=200, lines=None):
            self._json_data = json_data if json_data is not None else {}
            self.status = status
            self.content_type = "application/json"
            self._lines = lines or []

        @property
        def ok(self):
            return self.status < 400

        async def text(self):
            return json.dumps(self._json_data)

        async def json(self):
            return self._json_data

        @property
        def content(self):
            return _AsyncStreamIter(self._lines)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def request(self, method, url, **kwargs):
            return self._respond(method, url, kwargs)

        def get(self, url, **kwargs):
            return self._respond("GET", url, kwargs)

        def _respond(self, method, url, kwargs):
            calls.append({"method": method.upper(), "url": url, "json": kwargs.get("json")})
            if url.endswith("/apps/run") and method.upper() == "POST":
                body = kwargs.get("json") or {}
                return MockAsyncResponse(json_data={
                    "id": "task_async_sess",
                    "status": 1,
                    "session_id": "sess_async",
                    "input": body.get("input"),
                })
            if url.endswith("/tasks/task_async_sess/stream"):
                event_payload = json.dumps({
                    "id": "task_async_sess",
                    "status": 10,
                    "session_id": "sess_async",
                    "output": {"done": True},
                })
                return MockAsyncResponse(status=200, lines=[f"{event_payload}\n".encode()])
            if method.upper() == "DELETE":
                return MockAsyncResponse(status=204)
            return MockAsyncResponse(json_data={"id": "sess_async"})

    mock_aiohttp = MagicMock()
    mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
    mock_aiohttp.ClientSession = lambda **kwargs: MockClientSession()

    import inferencesh.client as client_mod

    async def require_aiohttp():
        return mock_aiohttp

    monkeypatch.setattr(client_mod, "_require_aiohttp", require_aiohttp)

    client = AsyncInference(api_key="test")
    async with await client.session("my-app@v1", input={"boot": True}) as session:
        assert session.session_id == "sess_async"
        result = await session.call("step", {"n": 2})

    assert result["output"] == {"done": True}
    run_calls = [c for c in calls if c["url"].endswith("/apps/run")]
    assert len(run_calls) == 2
    assert run_calls[0]["json"]["session"] == "new"
    assert run_calls[1]["json"]["session"] == "sess_async"
    assert any(c["method"] == "DELETE" for c in calls)


@pytest.mark.asyncio
async def test_async_session_handle_info_and_keepalive(monkeypatch):
    """AsyncSessionHandle.info/keepalive delegate to the async sessions namespace."""
    calls = []

    class MockAsyncResponse:
        def __init__(self, json_data=None, status=200):
            self._json_data = json_data if json_data is not None else {}
            self.status = status
            self.content_type = "application/json"

        @property
        def ok(self):
            return self.status < 400

        async def text(self):
            return json.dumps(self._json_data)

        async def json(self):
            return self._json_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def request(self, method, url, **kwargs):
            calls.append({"method": method.upper(), "url": url})
            if url.endswith("/keepalive"):
                return MockAsyncResponse({"id": "sess_async", "expires_at": "2099-06-01"})
            return MockAsyncResponse({"id": "sess_async", "status": "active"})

    mock_aiohttp = MagicMock()
    mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
    mock_aiohttp.ClientSession = lambda **kwargs: MockClientSession()

    import inferencesh.client as client_mod

    async def require_aiohttp():
        return mock_aiohttp

    monkeypatch.setattr(client_mod, "_require_aiohttp", require_aiohttp)

    from inferencesh.api.sessions import AsyncSessionHandle

    client = AsyncInference(api_key="test")
    handle = AsyncSessionHandle(client, "my-app@v1", "sess_async")

    info = await handle.info()
    assert info["id"] == "sess_async"

    kept = await handle.keepalive()
    assert kept["expires_at"] == "2099-06-01"

    assert any(c["url"].endswith("/sessions/sess_async") and c["method"] == "GET" for c in calls)
    assert any(c["url"].endswith("/keepalive") for c in calls)


@pytest.mark.asyncio
async def test_async_session_call_after_end_raises():
    client = AsyncInference(api_key="test")
    from inferencesh.api.sessions import AsyncSessionHandle

    handle = AsyncSessionHandle(client, "my-app@v1", "sess_async")
    handle._ended = True

    with pytest.raises(RuntimeError, match="Session has been ended"):
        await handle.call("step")
