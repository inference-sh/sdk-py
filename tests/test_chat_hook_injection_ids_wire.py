"""ChatHookEvent.injection_ids wire (e8d9ab4 / lifecycle hook stream UI).

Hook handlers that inject context messages must expose which message rows were
written so clients attach them to the run instead of listing them separately.
"""

import json
from typing import List, get_type_hints

from inferencesh.types import (
    ChatHookEvent,
    HookDecision,
    HookEvent,
    HookHandlerType,
)


def test_chat_hook_event_exposes_injection_ids():
    hints = get_type_hints(ChatHookEvent)
    assert hints["injection_ids"] == List[str]


def test_builtin_suggest_hook_reports_injection_message_ids():
    hook_row: ChatHookEvent = {
        "event": HookEvent.TURN_START,
        "handler_type": HookHandlerType.HOOK_HANDLER_BUILTIN,
        "handler": "suggest",
        "decision": HookDecision.ALLOW,
        "injected": True,
        "injection_ids": ["msg-inj-1", "msg-inj-2"],
        "duration_ms": 12,
    }
    assert hook_row["injection_ids"][0] == "msg-inj-1"
    assert hook_row["handler"] == "suggest"


def test_hook_without_injection_omits_injection_ids():
    hook_row: ChatHookEvent = {
        "event": HookEvent.AGENT_START,
        "handler_type": HookHandlerType.HOOK_HANDLER_WEBHOOK,
        "handler": "hooks.example.com",
        "decision": HookDecision.ALLOW,
        "injected": False,
    }
    assert "injection_ids" not in hook_row


def test_injection_ids_json_round_trip_as_string_list():
    payload = {
        "event": "agent.complete",
        "handler_type": "builtin",
        "handler": "extract",
        "injected": True,
        "injection_ids": ["a", "b"],
    }
    wire = json.loads(json.dumps(payload))
    typed: ChatHookEvent = {**wire}
    assert typed["injection_ids"] == ["a", "b"]
