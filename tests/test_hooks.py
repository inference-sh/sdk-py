"""Tests for the lifecycle hook builder."""

import json

from inferencesh.tools import lifecycle_hook
from inferencesh.types import BuiltinHook, HookEvent, HookHandlerType


class TestLifecycleHookBuilder:
    """Tests for lifecycle hook builder."""

    def test_webhook_produces_correct_config(self):
        hook = lifecycle_hook(HookEvent.AGENT_START).webhook("https://example.com/hook").build()

        assert hook["event"] == HookEvent.AGENT_START
        assert hook["type"] == HookHandlerType.HOOK_HANDLER_WEBHOOK
        assert hook["handler"] == "https://example.com/hook"

    def test_task_sets_handler_type(self):
        hook = lifecycle_hook(HookEvent.TURN_COMPLETE).task("acme/validator@v1").build()

        assert hook["type"] == HookHandlerType.HOOK_HANDLER_TASK
        assert hook["handler"] == "acme/validator@v1"

    def test_builtin_accepts_enum_or_wire_string(self):
        from_enum = lifecycle_hook(HookEvent.TURN_START).builtin(BuiltinHook.SUGGEST).build()
        from_str = lifecycle_hook(HookEvent.TURN_START).builtin("suggest").build()

        assert from_enum == from_str
        assert from_enum["type"] == HookHandlerType.HOOK_HANDLER_BUILTIN
        assert from_enum["handler"] == "suggest"

    def test_async_serializes_without_underscore(self):
        hook = lifecycle_hook(HookEvent.AGENT_START).webhook("https://example.com").async_(True).build()

        assert "async" in hook
        assert "async_" not in hook
        assert hook["async"] is True

    def test_built_hook_json_uses_wire_keys_and_string_enums(self):
        """Agent definitions are json.dumps'd before upload; enums must become wire strings."""
        hook = (
            lifecycle_hook(HookEvent.AGENT_START)
            .webhook("https://example.com/hook")
            .async_(True)
            .timeout(30)
            .build()
        )
        wire = json.loads(json.dumps(hook))
        assert wire == {
            "event": "agent.start",
            "type": "webhook",
            "handler": "https://example.com/hook",
            "async": True,
            "timeout": 30,
        }
        assert "async_" not in wire

    def test_timeout_is_included(self):
        hook = (
            lifecycle_hook(HookEvent.AGENT_START)
            .webhook("https://example.com")
            .timeout(30)
            .build()
        )

        assert hook["timeout"] == 30

    def test_minimal_build(self):
        hook = lifecycle_hook(HookEvent.TOOL_CALL).build()

        assert hook["event"] == HookEvent.TOOL_CALL
        assert "type" not in hook
        assert "handler" not in hook

    def test_builder_is_chainable(self):
        builder = lifecycle_hook(HookEvent.AGENT_START)

        assert builder.webhook("https://example.com") is builder
        assert builder.task("acme/agent@v1") is builder
        assert builder.async_(True) is builder
        assert builder.timeout(60) is builder
