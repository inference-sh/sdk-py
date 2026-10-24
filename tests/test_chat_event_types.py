"""Chat event wire types for event-role message content.

API chat streams surface run lifecycle as event content: clients must parse
``ChatEventType`` discriminators and read failure text from ``content.text`` or
structured run metadata from ``event.run`` on ``run_ended``.
"""

from typing import get_type_hints

from inferencesh.types import (
    AgentRunState,
    ChatEvent,
    ChatEventType,
    ChatMessageContent,
    ChatMessageContentType,
    ChatRunEvent,
    RunEndReason,
)


def test_chat_event_type_members_and_wire_values():
    assert ChatEventType.HOOK.value == "hook"
    assert ChatEventType.RUN_FAILED.value == "run_failed"
    assert ChatEventType.RUN_ENDED.value == "run_ended"
    assert set(ChatEventType.__members__) == {"HOOK", "RUN_FAILED", "RUN_ENDED"}


def test_chat_event_type_parses_wire_discriminators():
    assert ChatEventType("hook") is ChatEventType.HOOK
    assert ChatEventType("run_failed") is ChatEventType.RUN_FAILED
    assert ChatEventType("run_ended") is ChatEventType.RUN_ENDED


def test_run_end_reason_members_and_wire_values():
    assert RunEndReason.OUTPUT_LIMIT.value == "output_limit"
    assert RunEndReason.NO_REPLY.value == "no_reply"
    assert set(RunEndReason.__members__) == {"OUTPUT_LIMIT", "NO_REPLY"}


def test_chat_run_event_typed_dict_fields():
    hints = get_type_hints(ChatRunEvent)
    assert hints["run_id"] is str
    assert hints["state"] is AgentRunState
    assert hints["reason"] is RunEndReason

    run: ChatRunEvent = {
        "run_id": "run_abc",
        "state": AgentRunState.COMPLETED,
        "reason": RunEndReason.NO_REPLY,
    }
    assert run["state"] is AgentRunState.COMPLETED
    assert run["reason"] is RunEndReason.NO_REPLY


def test_chat_event_accepts_run_ended_payload():
    hints = get_type_hints(ChatEvent)
    assert hints["type"] is ChatEventType
    assert hints["run"] == ChatRunEvent | None  # type: ignore[valid-type]

    event: ChatEvent = {
        "type": ChatEventType.RUN_ENDED,
        "run": {
            "run_id": "run_xyz",
            "state": AgentRunState.CANCELED,
            "reason": RunEndReason.OUTPUT_LIMIT,
        },
    }
    assert event["type"] is ChatEventType.RUN_ENDED
    assert event["run"]["reason"] is RunEndReason.OUTPUT_LIMIT


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


def test_chat_message_content_carries_run_ended_event_with_optional_why_text():
    """RUN_ENDED describes how the run ended on event.run; text carries an optional why."""
    content: ChatMessageContent = {
        "type": ChatMessageContentType.EVENT,
        "text": "model produced no reply",
        "event": {
            "type": ChatEventType.RUN_ENDED,
            "run": {
                "run_id": "run_1",
                "state": AgentRunState.COMPLETED,
                "reason": RunEndReason.NO_REPLY,
            },
        },
    }
    assert content["event"]["type"] is ChatEventType.RUN_ENDED
    assert content["event"]["run"]["state"] is AgentRunState.COMPLETED
    assert content["text"] == "model produced no reply"
