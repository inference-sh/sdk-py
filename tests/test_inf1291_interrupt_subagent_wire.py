"""Sub-agent interrupt attribution and run reason (INF-1291 / 48b13c1 typegen).

Ancestor chats surface a sub-agent's pending question on their own card; ``origin``
names which sub-agent asked, and ``InterruptReason.SUBAGENT`` is the parent run's
wait reason (not an interrupt's ``reason``).
"""

from typing import List, Optional, get_type_hints

from inferencesh.types import (
    InterruptDTO,
    InterruptOrigin,
    InterruptReason,
    InterruptStatus,
)


def test_interrupt_origin_exposes_subagent_attribution_fields():
    hints = get_type_hints(InterruptOrigin)
    assert set(hints) >= {
        "agent_id",
        "agent_ref",
        "tool_invocation_id",
        "depth",
    }
    assert hints["agent_id"] is str
    assert hints["agent_ref"] is str
    assert hints["tool_invocation_id"] is str
    assert hints["depth"] is int


def test_interrupt_origin_models_delegated_subagent():
    origin: InterruptOrigin = {
        "agent_id": "agt_child",
        "agent_ref": "team/researcher",
        "tool_invocation_id": "inv_delegate_1",
        "depth": 1,
    }
    assert origin["agent_ref"] == "team/researcher"
    assert origin["depth"] == 1


def test_interrupt_dto_carries_optional_origin_on_ancestor_projection():
    hints = get_type_hints(InterruptDTO)
    assert hints["origin"] == Optional[InterruptOrigin]

    row: InterruptDTO = {
        "id": "int_sub",
        "chat_id": "chat_child",
        "reason": InterruptReason.TOOL_APPROVAL,
        "status": InterruptStatus.PENDING,
        "origin": {
            "agent_ref": "team/researcher",
            "tool_invocation_id": "inv_delegate_1",
            "depth": 1,
        },
    }
    assert row["origin"]["tool_invocation_id"] == "inv_delegate_1"
    assert row["chat_id"] == "chat_child"


def test_interrupt_reason_subagent_wire_value_is_run_level_only():
    """SUBAGENT labels a parent run waiting on a child; wire JSON is ``subagent``."""
    assert InterruptReason.SUBAGENT.value == "subagent"
    assert InterruptReason("subagent") is InterruptReason.SUBAGENT
    members = {m.value for m in InterruptReason}
    assert "subagent" in members