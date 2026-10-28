"""Builtin hook wire names and ChatHookEvent.injection_ids (e8d9ab4).

The platform renamed belt:* builtins to ``suggest`` / ``extract`` and added
``injection_ids`` on hook events so clients can tie injected messages to the
run. Builder tests in ``test_hooks`` / ``test_tools`` cover agent config;
these lock the stream/event DTO contract typegen must preserve.
"""

import json
from typing import List, get_type_hints

from inferencesh.types import (
    BuiltinHook,
    BuiltinHookDefinition,
    ChatEvent,
    ChatEventType,
    ChatHookEvent,
    ChatMessageContent,
    ChatMessageContentType,
    HookDecision,
    HookEvent,
    HookHandlerType,
)


def test_builtin_hook_enum_wire_values():
    assert BuiltinHook.SUGGEST.value == "suggest"
    assert BuiltinHook.EXTRACT.value == "extract"
    assert set(h.value for h in BuiltinHook) == {"suggest", "extract"}


def test_builtin_hook_parses_from_api_strings():
    assert BuiltinHook("suggest") is BuiltinHook.SUGGEST
    assert BuiltinHook("extract") is BuiltinHook.EXTRACT


def test_builtin_hook_serializes_stable_wire_strings():
    for hook in BuiltinHook:
        assert json.loads(json.dumps(hook)) == hook.value


def test_chat_hook_event_declares_injection_ids():
    hints = get_type_hints(ChatHookEvent)
    assert hints["injection_ids"] == List[str]


def test_chat_hook_event_injection_ids_round_trip_in_message_content():
    content: ChatMessageContent = {
        "type": ChatMessageContentType.EVENT,
        "event": {
            "type": ChatEventType.HOOK,
            "hook": {
                "event": HookEvent.TURN_START,
                "handler_type": HookHandlerType.HOOK_HANDLER_BUILTIN,
                "handler": BuiltinHook.SUGGEST.value,
                "decision": HookDecision.ALLOW,
                "injected": True,
                "injection_ids": ["inj_01", "inj_02"],
                "duration_ms": 48,
            },
        },
    }
    wire = json.loads(json.dumps(content))
    hook = wire["event"]["hook"]
    assert hook["handler"] == "suggest"
    assert hook["injection_ids"] == ["inj_01", "inj_02"]

    parsed: ChatHookEvent = content["event"]["hook"]  # type: ignore[index]
    assert parsed["injection_ids"][0] == "inj_01"


def test_builtin_hook_definition_uses_enum_name():
    hints = get_type_hints(BuiltinHookDefinition)
    assert hints["name"] is BuiltinHook
    definition: BuiltinHookDefinition = {
        "name": BuiltinHook.EXTRACT,
        "description": "Learn from the conversation",
        "events": [HookEvent.AGENT_COMPLETE, HookEvent.PRE_COMPACT],
    }
    assert definition["name"] is BuiltinHook.EXTRACT


def test_chat_event_still_pairs_hook_with_run_slot():
    """Regression: adding hook fields must not drop the run_ended sibling."""
    hints = get_type_hints(ChatEvent)
    assert "hook" in hints and "run" in hints
