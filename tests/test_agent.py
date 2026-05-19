"""Tests for headless Agent client (context wiring, /agents/run payloads)."""

import json

import pytest

from inferencesh import Inference


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

        return DummyResponse(status_code=404, json_data={"success": False, "error": {"message": "not found"}})

    class FakeRequestsModule:
        def request(self, *args, **kwargs):
            return fake_request(*args, **kwargs)

    fake_requests = FakeRequestsModule()

    import inferencesh.agent as agent_mod

    monkeypatch.setattr(agent_mod, "_require_requests", lambda: fake_requests)

    yield calls


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
