"""Agent run wire contract: MessageInput and ApiAgentRunRequest (v0.8.91 typegen).

POST /agents/run no longer accepts an LLMInput envelope or CreateAgentMessageRequest;
the SDK must send MessageInput (text + attachments) inside ApiAgentRunRequest.
"""

from typing import get_type_hints

import pytest

from inferencesh import types as types_mod
from inferencesh.agent import _run_body
from inferencesh.types import ApiAgentRunRequest, ContextField, FileRef, MessageInput, Scope, ScopeGroup


MESSAGE_INPUT_KEYS = frozenset({"text", "attachments", "images", "files"})


def test_message_input_fields_match_typegen():
    hints = get_type_hints(MessageInput)
    assert set(hints) == MESSAGE_INPUT_KEYS


def test_create_agent_message_request_removed_from_types():
    assert not hasattr(types_mod, "CreateAgentMessageRequest")


def test_api_agent_run_request_input_is_message_input():
    hints = get_type_hints(ApiAgentRunRequest)
    assert hints["input"] is MessageInput
    assert "channel_context" not in hints


def test_context_field_supports_in_prompt_flag():
    hints = get_type_hints(ContextField)
    assert hints["in_prompt"] is bool

    field: ContextField = {
        "name": "user_id",
        "description": "Caller user id",
        "required": True,
        "in_prompt": True,
    }
    assert field["in_prompt"] is True


def test_store_scopes_replaced_admin_pricing():
    values = {m.value for m in Scope}
    assert Scope.STORE_PRICING.value == "store:pricing"
    assert Scope.STORE_SUBMIT.value == "store:submit"
    assert ScopeGroup.STORE.value == "store"
    assert "admin:pricing" not in values
    assert not hasattr(Scope, "ADMIN_PRICING")


def test_run_body_input_is_message_input_only():
    body = _run_body("okaris/assistant@abc", None, {"k": "v"}, "Hello", None, None)
    assert set(body["input"]) <= MESSAGE_INPUT_KEYS
    assert body["input"]["text"] == "Hello"
    assert "role" not in body["input"]
    assert "system_prompt" not in body["input"]


def test_run_body_includes_attachments_when_provided():
    attachments: list[FileRef] = [{"uri": "https://example.com/f.bin"}]
    body = _run_body("okaris/assistant@abc", None, None, "See file", attachments, None)
    assert body["input"]["attachments"] == attachments


@pytest.mark.parametrize(
    "channel_context",
    [
        None,
        {"channel": "slack", "thread_id": "T1"},
    ],
)
def test_run_body_still_forwards_channel_context_when_set(channel_context):
    """Extra run fields may outpace typegen; SDK keeps forwarding channel_context."""
    body = _run_body("okaris/assistant@abc", None, None, "Hi", None, channel_context)
    if channel_context is None:
        assert "channel_context" not in body
    else:
        assert body["channel_context"] == channel_context
