"""Wire contracts for RunEndReasonRefusal (656006d typegen).

Safety refusals surface on run_ended chat events; the enum value must stay
aligned with the API and deserialize into ChatRunEvent payloads.
"""

import json

from inferencesh.types import ChatEventType, ChatRunEvent, RunEndReason


def test_run_end_reason_refusal_wire_value():
    assert RunEndReason.REFUSAL.value == "refusal"
    assert RunEndReason("refusal") is RunEndReason.REFUSAL


def test_run_end_reason_members():
    assert {m.value for m in RunEndReason} == {
        "output_limit",
        "no_reply",
        "refusal",
    }


def test_chat_run_event_refusal_json_round_trip():
    event: ChatRunEvent = {
        "run_id": "run_abc",
        "reason": RunEndReason.REFUSAL,
        "duration_ms": 1200,
    }
    payload = json.loads(json.dumps(event, default=lambda o: o.value))
    assert payload["reason"] == "refusal"
    assert payload["run_id"] == "run_abc"
    assert payload["duration_ms"] == 1200

    restored: ChatRunEvent = json.loads(json.dumps(payload))
    assert restored["reason"] == "refusal"


def test_chat_event_type_run_ended_wire_value():
    assert ChatEventType.RUN_ENDED.value == "run_ended"
