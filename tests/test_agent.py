"""Tests for headless Agent client (context wiring, /agents/run payloads)."""

import base64
import json

import pytest

from inferencesh import Inference, AsyncInference


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {"success": True, "data": {}}
        self.text = text if text is not None else json.dumps(self._json_data)

    @property
    def ok(self):
        return 200 <= self.status_code < 300


@pytest.fixture
def patch_agent_requests(monkeypatch):
    """Capture Agent HTTP calls without hitting the network."""
    calls = []

    def fake_request(method, url, params=None, data=None, headers=None, stream=False, timeout=None):
        calls.append({
            "method": method,
            "url": url,
            "data": json.loads(data) if data else None,
        })

        if url.endswith("/agents/run") and method.upper() == "POST":
            body = calls[-1]["data"]
            return DummyResponse(json_data={
                "success": True,
                "data": {
                    "assistant_message": {
                        "id": "msg_1",
                        "chat_id": "chat_1",
                        "text": "Hi",
                        "role": "assistant",
                        "context": body.get("context"),
                    },
                },
            })

        if "/tools/" in url and method.upper() == "POST":
            return DummyResponse(json_data={"success": True, "data": None})

        if url.endswith("/files") and method.upper() == "POST":
            return DummyResponse(json_data={
                "success": True,
                "data": [{
                    "id": "file_agent_1",
                    "uri": "https://cloud.inference.sh/u/user/file_agent_1.bin",
                    "upload_url": "https://upload.example.com/agent-file",
                    "filename": "attach.bin",
                    "content_type": "application/octet-stream",
                }],
            })

        if "/chats/" in url and method.upper() == "GET":
            chat_id = url.rstrip("/").split("/")[-1]
            return DummyResponse(json_data={
                "success": True,
                "data": {
                    "id": chat_id,
                    "status": "idle",
                    "output": {"result": "done"},
                },
            })

        if "/chats/" in url and url.endswith("/stop") and method.upper() == "POST":
            return DummyResponse(json_data={"success": True, "data": None})

        return DummyResponse(status_code=404, json_data={"success": False, "error": {"message": "not found"}})

    class FakeRequestsModule:
        def __init__(self, call_log):
            self.calls = call_log
            self.put_calls = []

        def __getitem__(self, index):
            return self.calls[index]

        def __len__(self):
            return len(self.calls)

        def request(self, *args, **kwargs):
            return fake_request(*args, **kwargs)

        def put(self, url, data=None, headers=None):
            self.put_calls.append({"url": url, "size": len(data or b""), "headers": headers})
            return DummyResponse(status_code=200)

    fake_requests = FakeRequestsModule(calls)

    import inferencesh.agent as agent_mod

    monkeypatch.setattr(agent_mod, "_require_requests", lambda: fake_requests)

    yield fake_requests


def test_agent_template_ref_includes_context(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123", context={"user_id": "u-1", "locale": "en"})

    msg = agent.send_message("Hello")

    assert msg["text"] == "Hi"
    body = patch_agent_requests[0]["data"]
    assert body["agent"] == "okaris/assistant@abc123"
    assert body["context"] == {"user_id": "u-1", "locale": "en"}
    assert body["input"]["text"] == "Hello"


def test_agent_ad_hoc_config_includes_context(patch_agent_requests):
    client = Inference(api_key="test")
    config = {
        "name": "helper",
        "core_app": {"ref": "infsh/claude-sonnet-4@xyz"},
        "system_prompt": "You are helpful",
    }
    agent = client.agent(config, context={"tenant": "acme"})

    agent.send_message("Run query")

    body = patch_agent_requests[0]["data"]
    assert body["agent_config"] == config
    assert body["agent_name"] == "helper"
    assert body["context"] == {"tenant": "acme"}


def test_agents_create_delegates_to_client_agent(patch_agent_requests):
    """client.agents.create() returns an agent that can call /agents/run."""
    client = Inference(api_key="test")
    agent = client.agents.create("okaris/assistant@abc123")
    agent.send_message("Hi")

    body = patch_agent_requests[0]["data"]
    assert body["agent"] == "okaris/assistant@abc123"


def test_agent_without_context_sends_none(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    agent.send_message("Hi")

    body = patch_agent_requests[0]["data"]
    assert body["context"] is None


def test_submit_tool_result_string_payload(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    agent.submit_tool_result("inv_1", '{"ok": true}')

    tool_call = patch_agent_requests[-1]
    assert tool_call["method"] == "POST"
    assert tool_call["url"].endswith("/tools/inv_1")
    assert tool_call["data"] == {"result": '{"ok": true}'}


def test_submit_tool_result_widget_action_json(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    payload = {"action": {"type": "confirm"}, "form_data": {"name": "Ada"}}
    agent.submit_tool_result("inv_2", payload)

    assert patch_agent_requests[-1]["data"] == {
        "result": json.dumps(payload),
    }


def test_stream_all_dispatches_client_tool_once(monkeypatch, patch_agent_requests):
    from inferencesh.types import ToolInvocationStatus, ToolType

    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")
    assert agent.chat_id == "chat_1"

    inv = {
        "id": "inv_dup",
        "type": ToolType.CLIENT,
        "status": ToolInvocationStatus.AWAITING_INPUT,
        "function": {"name": "ask_user", "arguments": {"q": "name?"}},
    }

    events = [
        ("chat_messages", {"tool_invocations": [inv]}),
        ("chat_messages", {"tool_invocations": [inv]}),
        ("chats", {"active_run": {"state": "completed"}}),
    ]

    def fake_typed_stream(endpoint):
        assert endpoint == "/chats/chat_1/stream"
        return iter(events)

    monkeypatch.setattr(agent, "_create_typed_ndjson_generator", fake_typed_stream)

    seen = []
    agent.stream_all(on_tool_call=lambda info: seen.append(info.id))

    assert seen == ["inv_dup"]


@pytest.mark.parametrize(
    "terminal_state",
    [
        "completed",
        "failed",
        "canceled",
        "input_required",
        "auth_required",
        "rejected",
    ],
)
def test_stream_all_stops_on_terminal_active_run_state(
    monkeypatch, patch_agent_requests, terminal_state,
):
    """stream_all stops when active_run.state is not working/submitted (45608aa)."""
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    events = [
        ("chat_messages", {"id": "msg_1", "text": "Hi", "role": "assistant"}),
        ("chats", {"active_run": {"state": terminal_state}}),
        ("chat_messages", {"id": "msg_2", "text": "after terminal", "role": "assistant"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    messages = []
    agent.stream_all(on_message=lambda msg: messages.append(msg["id"]))

    assert messages == ["msg_1"]


def test_stream_all_stops_when_active_run_missing(monkeypatch, patch_agent_requests):
    """No active_run means the agent run finished — stream_all must stop."""
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    events = [
        ("chat_messages", {"id": "msg_1", "text": "Hi", "role": "assistant"}),
        ("chats", {"id": "chat_1"}),
        ("chat_messages", {"id": "msg_2", "text": "after idle", "role": "assistant"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    messages = []
    agent.stream_all(on_message=lambda msg: messages.append(msg["id"]))

    assert messages == ["msg_1"]


def test_stream_all_continues_while_active_run_is_working_or_submitted(
    monkeypatch, patch_agent_requests,
):
    """stream_all keeps reading until active_run.state leaves working/submitted."""
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    events = [
        ("chats", {"active_run": {"state": "working"}}),
        ("chat_messages", {"id": "msg_1", "text": "partial", "role": "assistant"}),
        ("chats", {"active_run": {"state": "submitted"}}),
        ("chat_messages", {"id": "msg_2", "text": "more", "role": "assistant"}),
        ("chats", {"active_run": {"state": "completed"}}),
        ("chat_messages", {"id": "msg_3", "text": "after terminal", "role": "assistant"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    messages = []
    chats = []
    agent.stream_all(
        on_chat=lambda chat: chats.append(chat.get("active_run", {}).get("state")),
        on_message=lambda msg: messages.append(msg["id"]),
    )

    assert messages == ["msg_1", "msg_2"]
    assert chats == ["working", "submitted", "completed"]


def test_stream_all_ignores_legacy_chat_status_field(monkeypatch, patch_agent_requests):
    """Termination must use active_run.state, not the derived chat status field."""
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    events = [
        ("chats", {"status": "idle", "active_run": {"state": "working"}}),
        ("chat_messages", {"id": "msg_1", "text": "still running", "role": "assistant"}),
        ("chats", {"status": "busy", "active_run": {"state": "completed"}}),
        ("chat_messages", {"id": "msg_2", "text": "after terminal", "role": "assistant"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    messages = []
    agent.stream_all(on_message=lambda msg: messages.append(msg["id"]))

    assert messages == ["msg_1"]


@pytest.mark.asyncio
async def test_async_agent_stream_messages_yields_chat_message_events(monkeypatch, patch_agent_requests):
    from inferencesh import AsyncInference

    client = AsyncInference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    async def fake_send(text, **kwargs):
        agent._chat_id = "chat_1"
        return {"id": "msg_1", "chat_id": "chat_1", "text": "Hi", "role": "assistant"}

    async def fake_stream(endpoint):
        assert endpoint == "/chats/chat_1/stream"
        yield ("chat_messages", {"id": "msg_2", "text": "Update", "role": "assistant"})
        yield ("chats", {"id": "chat_1", "status": "idle"})

    monkeypatch.setattr(agent, "send_message", fake_send)
    monkeypatch.setattr(agent, "_stream_typed_ndjson", fake_stream)

    await agent.send_message("Hi")
    messages = [msg async for msg in agent.stream_messages()]

    assert len(messages) == 1
    assert messages[0]["text"] == "Update"


@pytest.mark.asyncio
async def test_async_agent_stream_chat_yields_chat_events(monkeypatch, patch_agent_requests):
    from inferencesh import AsyncInference

    client = AsyncInference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    async def fake_send(text, **kwargs):
        agent._chat_id = "chat_1"
        return {"id": "msg_1", "chat_id": "chat_1", "text": "Hi", "role": "assistant"}

    async def fake_stream(endpoint):
        yield ("chat_messages", {"id": "msg_1", "text": "Hi", "role": "assistant"})
        yield ("chats", {"id": "chat_1", "status": "busy"})
        yield ("chats", {"id": "chat_1", "status": "idle"})

    monkeypatch.setattr(agent, "send_message", fake_send)
    monkeypatch.setattr(agent, "_stream_typed_ndjson", fake_stream)

    await agent.send_message("Hi")
    chats = [chat async for chat in agent.stream_chat()]

    assert len(chats) == 2
    assert chats[0]["status"] == "busy"
    assert chats[1]["status"] == "idle"


@pytest.mark.asyncio
async def test_async_agent_stream_requires_active_chat(monkeypatch):
    client = AsyncInference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    with pytest.raises(RuntimeError, match="No active chat"):
        async for _ in agent.stream_messages():
            pass


def test_agent_run_returns_chat_output(monkeypatch, patch_agent_requests):
    """agent.run() returns parsed finish-tool output from the active chat."""
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    monkeypatch.setattr(agent, "send_message", lambda text, **kwargs: {"chat_id": "chat_1"})
    monkeypatch.setattr(agent, "get_chat", lambda chat_id=None: {"output": {"answer": 42}})

    assert agent.run("finish task") == {"answer": 42}


def test_agent_run_returns_none_when_chat_has_no_output(monkeypatch, patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    monkeypatch.setattr(agent, "send_message", lambda text, **kwargs: None)
    monkeypatch.setattr(agent, "get_chat", lambda chat_id=None: {"status": "idle"})

    assert agent.run("query") is None


def test_agent_reset_clears_chat_and_dispatched_tools(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")
    agent._dispatched_tools.add("inv_old")

    agent.reset()

    assert agent.chat_id is None
    assert agent._dispatched_tools == set()


def test_agent_upload_file_from_bytes(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    ref = agent.upload_file(b"attach-bytes", filename="note.txt")

    assert ref["uri"] == "https://cloud.inference.sh/u/user/file_agent_1.bin"
    assert ref["filename"] == "attach.bin"
    assert len(patch_agent_requests.put_calls) == 1
    assert patch_agent_requests.put_calls[0]["size"] == len(b"attach-bytes")


def test_agent_upload_file_from_data_uri(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    payload = base64.b64encode(b"hello").decode()
    data_uri = f"data:text/plain;base64,{payload}"

    agent.upload_file(data_uri)

    assert patch_agent_requests.put_calls[0]["size"] == len(b"hello")
    assert patch_agent_requests.put_calls[0]["headers"]["Content-Type"] == "text/plain"


def test_agent_upload_file_rejects_invalid_data_uri(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    with pytest.raises(ValueError, match="Invalid data URI"):
        agent.upload_file("data:not-valid")


def test_agent_send_message_uploads_file_attachments(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    agent.send_message("See file", files=[b"raw-bytes"])

    file_posts = [c for c in patch_agent_requests.calls if c["url"].endswith("/files")]
    assert len(file_posts) == 1
    assert len(patch_agent_requests.put_calls) == 1

    run_body = next(c["data"] for c in patch_agent_requests.calls if c["url"].endswith("/agents/run"))
    attachments = run_body["input"]["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["uri"] == "https://cloud.inference.sh/u/user/file_agent_1.bin"


def test_async_agents_create_returns_async_agent():
    """AsyncInference.agents.create() delegates to client.agent()."""
    from inferencesh.agent import AsyncAgent

    client = AsyncInference(api_key="test")
    agent = client.agents.create("okaris/assistant@abc123")

    assert isinstance(agent, AsyncAgent)
    assert agent._options == "okaris/assistant@abc123"


class _ImmediateStreamManager:
    """Run StreamManager callbacks synchronously (avoids reconnect sleeps in unit tests)."""

    def __init__(self, *, create_event_source, on_data=None, on_error=None, on_stop=None, **kwargs):
        self._events = list(create_event_source())
        self._on_data = on_data
        self._on_stop = on_stop

    def connect(self):
        for event in self._events:
            if self._on_data:
                self._on_data(event)
        if self._on_stop:
            self._on_stop()

    def stop(self):
        if self._on_stop:
            self._on_stop()


def test_agent_stream_messages_yields_chat_message_events(monkeypatch, patch_agent_requests):
    import inferencesh.agent as agent_mod

    monkeypatch.setattr(agent_mod, "StreamManager", _ImmediateStreamManager)

    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")
    assert agent.chat_id == "chat_1"

    events = [
        ("chat_messages", {"id": "msg_2", "text": "Update", "role": "assistant"}),
        ("chats", {"id": "chat_1", "status": "idle"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    messages = list(agent.stream_messages())

    assert len(messages) == 1
    assert messages[0]["text"] == "Update"


def test_agent_stream_chat_yields_chat_events(monkeypatch, patch_agent_requests):
    import inferencesh.agent as agent_mod

    monkeypatch.setattr(agent_mod, "StreamManager", _ImmediateStreamManager)

    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    events = [
        ("chat_messages", {"id": "msg_1", "text": "Hi", "role": "assistant"}),
        ("chats", {"id": "chat_1", "status": "busy"}),
        ("chats", {"id": "chat_1", "status": "idle"}),
    ]

    monkeypatch.setattr(
        agent,
        "_create_typed_ndjson_generator",
        lambda endpoint: iter(events),
    )

    chats = list(agent.stream_chat())

    assert len(chats) == 2
    assert chats[0]["status"] == "busy"
    assert chats[1]["status"] == "idle"


def test_agent_stream_requires_active_chat():
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    with pytest.raises(RuntimeError, match="No active chat"):
        list(agent.stream_messages())


def test_agent_stop_chat_posts_to_endpoint(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    agent.stop_chat()

    stop_call = patch_agent_requests[-1]
    assert stop_call["method"] == "POST"
    assert stop_call["url"].endswith("/chats/chat_1/stop")


def test_agent_get_chat_without_chat_id_returns_none(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    assert agent.get_chat() is None


def test_agent_get_chat_fetches_by_id(patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")
    agent.send_message("Hi")

    chat = agent.get_chat()

    assert chat["id"] == "chat_1"
    assert chat["output"] == {"result": "done"}
    get_call = patch_agent_requests[-1]
    assert get_call["method"] == "GET"
    assert get_call["url"].endswith("/chats/chat_1")


def test_agent_send_message_invokes_streaming_callbacks(monkeypatch, patch_agent_requests):
    client = Inference(api_key="test")
    agent = client.agent("okaris/assistant@abc123")

    streamed = {"called": False}

    def fake_stream_all(**kwargs):
        streamed["called"] = True
        streamed["on_message"] = kwargs.get("on_message") is not None
        streamed["on_tool_call"] = kwargs.get("on_tool_call") is not None

    monkeypatch.setattr(agent, "stream_all", fake_stream_all)

    agent.send_message("Hi", on_message=lambda msg: None, on_tool_call=lambda info: None)

    assert streamed["called"] is True
    assert streamed["on_message"] is True
    assert streamed["on_tool_call"] is True
