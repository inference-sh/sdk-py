"""Chat event wire types for event-role message content (ChatEventType.RUN_FAILED).

API chat streams can surface run failures as event content; clients must parse
the run_failed discriminator and read the error from the sibling text field.
"""

from typing import get_type_hints

from inferencesh.types import (
    ChatEvent,
    ChatEventType,
    ChatMessageContent,
    ChatMessageContentType,
)


def test_chat_event_type_members_and_wire_values():
    assert ChatEventType.HOOK.value == "hook"
    assert ChatEventType.RUN_FAILED.value == "run_failed"
    assert set(ChatEventType.__members__) == {"HOOK", "RUN_FAILED"}


def test_chat_event_type_parses_run_failed_from_wire():
    assert ChatEventType("run_failed") is ChatEventType.RUN_FAILED
    assert ChatEventType("hook") is ChatEventType.HOOK


def test_chat_event_typed_dict_accepts_run_failed():
    hints = get_type_hints(ChatEvent)
    assert hints["type"] is ChatEventType

    event: ChatEvent = {"type": ChatEventType.RUN_FAILED}
    assert event["type"] is ChatEventType.RUN_FAILED


def test_chat_message_content_carries_run_failed_event_with_error_text():
    """RUN_FAILED marks failure; the error string lives in content.text, not on ChatEvent."""
    hints = get_type_hints(ChatMessageContent)
    assert hints["type"] is ChatMessageContentType
    assert hints["event"] == ChatEvent | None  # type: ignore[valid-type]

    content: ChatMessageContent = {
        "type": ChatMessageContentType.EVENT,
        "text": "upstream timeout",
        "event": {"type": ChatEventType.RUN_FAILED},
    }
    assert content["event"]["type"] is ChatEventType.RUN_FAILED
    assert content["text"] == "upstream timeout"
