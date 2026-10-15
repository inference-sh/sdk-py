"""Gotypegen reserved JSON keys and TypedDict _field_tags (6f45a3b).

Go API fields named ``in`` and ``async`` must appear on the wire under those
names, not Python-safe ``in_`` / ``async_``. Delta merge tags on generated
TypedDicts must survive gotypegen moving ``_field_tags`` outside class bodies.
"""

from typing import get_type_hints

from inferencesh.delta import _get_field_tags
from inferencesh.types import (
    AuthMethod,
    AuthMethodAPIKeyIn,
    AuthMethodKind,
    HookEvent,
    HookHandlerType,
    LifecycleHookConfig,
    LLMDelta,
    ToolCallDelta,
    ToolCallFunctionDelta,
)


def test_auth_method_declares_wire_key_in_not_in_underscore():
    hints = get_type_hints(AuthMethod)
    assert "in" in hints
    assert "in_" not in hints
    assert hints["in"] is AuthMethodAPIKeyIn


def test_auth_method_api_key_payload_round_trips_in_key():
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_API_KEY,
        "in": AuthMethodAPIKeyIn.HEADER,
        "param_name": "X-Api-Key",
    }
    assert method["in"] is AuthMethodAPIKeyIn.HEADER
    assert method["in"].value == "header"
    assert "in_" not in method


def test_lifecycle_hook_config_declares_wire_key_async_not_async_underscore():
    hints = get_type_hints(LifecycleHookConfig)
    assert "async" in hints
    assert hints["async"] is bool
    assert "async_" not in hints


def test_lifecycle_hook_config_accepts_async_wire_key():
    config: LifecycleHookConfig = {
        "event": HookEvent.AGENT_START,
        "type": HookHandlerType.HOOK_HANDLER_WEBHOOK,
        "handler": "https://example.com/hook",
        "async": True,
        "timeout": 30,
    }
    assert config["async"] is True
    assert "async_" not in config


def test_generated_typed_dict_deltas_expose_field_tags_on_class():
    assert LLMDelta._field_tags["response"]["merge"] == "concat"
    assert LLMDelta._field_tags["tool_calls"]["merge"] == "indexed"
    assert ToolCallFunctionDelta._field_tags["arguments"]["merge"] == "concat"
    assert ToolCallDelta._field_tags["function"]["merge"] == "nested"


def test_delta_module_reads_field_tags_from_typed_dict_class():
    """merge_delta cannot infer tags from plain dict instances; the class must carry them."""
    tags = _get_field_tags(LLMDelta)
    assert tags["response"]["merge"] == "concat"
    assert tags["tool_calls"]["merge"] == "indexed"
