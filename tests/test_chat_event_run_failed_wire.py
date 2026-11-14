"""ChatEventType.RUN_FAILED wire (3ae8677 / failed agent run markers).

Event-role chat messages mark where a run failed; stream clients must accept the
``run_failed`` type without treating it as an unknown event.
"""

import json
from typing import get_type_hints

from inferencesh.types import ChatEvent, ChatEventType, ChatRunEvent, RunEndReason


def test_chat_event_type_includes_run_failed():
    assert ChatEventType.RUN_FAILED.value == "run_failed"
    assert ChatEventType.RUN_FAILED in ChatEventType


def test_chat_event_typedict_accepts_run_failed_type():
    hints = get_type_hints(ChatEvent)
    assert hints["type"] is ChatEventType

    payload: ChatEvent = {
        "type": ChatEventType.RUN_FAILED,
    }
    assert payload["type"] is ChatEventType.RUN_FAILED


def test_run_failed_serializes_to_wire_string():
    payload: ChatEvent = {"type": ChatEventType.RUN_FAILED}
    wire = json.loads(json.dumps(payload))
    assert wire["type"] == "run_failed"


def test_run_failed_is_distinct_from_run_ended():
    assert ChatEventType.RUN_FAILED.value != ChatEventType.RUN_ENDED.value
    run_block: ChatRunEvent = {
        "run_id": "run-1",
        "reason": RunEndReason.NO_REPLY,
        "duration_ms": 100,
    }
    ended: ChatEvent = {"type": ChatEventType.RUN_ENDED, "run": run_block}
    failed: ChatEvent = {"type": ChatEventType.RUN_FAILED}
    assert ended["type"] is not failed["type"]
