"""Chat event hook payloads and RunEndReason wire parsing (fafc131 complement).

Draft #652 covers RUN_ENDED / RUN_FAILED content shapes and ``Infra.remote``.
These tests lock the pre-existing HOOK event path and ``RunEndReason`` parsing
so typegen cannot drop ``ChatEvent.hook`` when adding ``ChatEvent.run``.
"""

import json
from typing import get_type_hints

from inferencesh.types import (
    ChatEvent,
    ChatEventType,
    ChatHookEvent,
    ChatRunEvent,
    ChatMessageContent,
    ChatMessageContentType,
    HookDecision,
    HookEvent,
    HookHandlerType,
    RunEndReason,
)


def test_chat_event_typed_dict_includes_hook_and_run():
    hints = get_type_hints(ChatEvent)
    assert hints["type"] is ChatEventType
    assert hints["hook"] == ChatHookEvent | None  # type: ignore[valid-type]
    assert hints["run"] == ChatRunEvent | None  # type: ignore[valid-type]


def test_chat_hook_event_typed_dict_fields():
    hints = get_type_hints(ChatHookEvent)
    assert hints["event"] is HookEvent
    assert hints["handler_type"] is HookHandlerType
    assert hints["handler"] is str
    assert hints["decision"] is HookDecision

    hook: ChatHookEvent = {
        "event": HookEvent.TOOL_CALL,
        "handler_type": HookHandlerType.HOOK_HANDLER_BUILTIN,
        "handler": "belt_suggest",
        "decision": HookDecision.ALLOW,
        "reason": "policy ok",
        "injected": True,
        "duration_ms": 12,
    }
    assert hook["decision"] is HookDecision.ALLOW


def test_chat_message_content_carries_hook_event():
    content: ChatMessageContent = {
        "type": ChatMessageContentType.EVENT,
        "event": {
            "type": ChatEventType.HOOK,
            "hook": {
                "event": HookEvent.AGENT_COMPLETE,
                "handler_type": HookHandlerType.HOOK_HANDLER_GATE,
                "handler": "approval_gate",
                "decision": HookDecision.SUSPEND,
                "reason": "awaiting approval",
            },
        },
    }
    assert content["event"]["type"] is ChatEventType.HOOK
    assert content["event"]["hook"]["decision"] is HookDecision.SUSPEND


def test_run_end_reason_parses_wire_discriminators():
    assert RunEndReason("output_limit") is RunEndReason.OUTPUT_LIMIT
    assert RunEndReason("no_reply") is RunEndReason.NO_REPLY


def test_run_end_reason_serializes_stable_wire_strings():
    for reason in RunEndReason:
        assert json.loads(json.dumps(reason)) == reason.value
