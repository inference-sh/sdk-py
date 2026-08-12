"""Tests for the lifecycle hook builder."""

import inferencesh
from inferencesh.tools import lifecycle_hook, LifecycleHookBuilder
from inferencesh.types import AgentConfigInput, HookEvent, HookHandlerType


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

    def test_async_serializes_without_underscore(self):
        hook = lifecycle_hook(HookEvent.AGENT_START).webhook("https://example.com").async_(True).build()

        assert "async" in hook
        assert "async_" not in hook
        assert hook["async"] is True

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

    def test_importable_from_top_level_package(self):
        """lifecycle_hook and hook types are part of the public SDK surface."""
        assert inferencesh.lifecycle_hook is lifecycle_hook
        assert inferencesh.LifecycleHookBuilder is LifecycleHookBuilder
        assert inferencesh.HookEvent is HookEvent
        assert inferencesh.HookHandlerType is HookHandlerType

    def test_task_overrides_prior_webhook_handler(self):
        """The last handler method wins when builders are chained."""
        hook = (
            lifecycle_hook(HookEvent.TOOL_RESULT)
            .webhook("https://example.com/webhook")
            .task("acme/validator@v2")
            .build()
        )

        assert hook["type"] == HookHandlerType.HOOK_HANDLER_TASK
        assert hook["handler"] == "acme/validator@v2"

    def test_builder_output_fits_agent_config_hooks(self):
        """AgentConfigInput.hooks accepts lifecycle_hook().build() output."""
        config: AgentConfigInput = {
            "name": "audited-agent",
            "hooks": [
                lifecycle_hook(HookEvent.AGENT_START).webhook("https://example.com/start").build(),
                lifecycle_hook(HookEvent.TOOL_CALL).task("acme/policy-check@v1").timeout(15).build(),
            ],
        }

        assert len(config["hooks"]) == 2
        assert config["hooks"][0]["event"] == HookEvent.AGENT_START
        assert config["hooks"][1]["type"] == HookHandlerType.HOOK_HANDLER_TASK
        assert config["hooks"][1]["timeout"] == 15
