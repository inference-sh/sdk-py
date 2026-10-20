"""Agent tool approval timeout, internal wait tool, InterruptReason.WAIT (a6c9879).

Models v0.8.122 adds ``approval_timeout`` on agent tools, ``wait`` on
``InternalToolsConfig``, and ``InterruptReason.WAIT`` for deadline-based pauses.
"""

import json
from typing import Optional, get_type_hints

import pytest

from inferencesh import pending_approvals
from inferencesh.types import (
    AgentTool,
    AgentToolDTO,
    InternalToolsConfig,
    InterruptReason,
    InterruptStatus,
    ToolType,
)


def test_agent_tool_declares_approval_timeout():
    for cls in (AgentTool, AgentToolDTO):
        hints = get_type_hints(cls)
        assert "approval_timeout" in hints
        assert hints["approval_timeout"] is int


def test_agent_tool_approval_timeout_round_trips_wire_json():
    tool: AgentTool = {
        "name": "deploy",
        "type": ToolType.HTTP,
        "require_approval": True,
        "approval_timeout": 120,
        "http": {"url": "https://api.example.com/deploy"},
    }
    wire = json.loads(json.dumps(tool, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["approval_timeout"] == 120
    assert wire["require_approval"] is True
    restored: AgentTool = wire  # type: ignore[assignment]
    assert restored["approval_timeout"] == 120


def test_internal_tools_config_declares_wait_toggle():
    hints = get_type_hints(InternalToolsConfig)
    assert "wait" in hints
    assert hints["wait"] == Optional[bool]


def test_internal_tools_config_wait_round_trips_wire_json():
    cfg: InternalToolsConfig = {"plan": True, "wait": True}
    wire = json.loads(json.dumps(cfg))
    assert wire == {"plan": True, "wait": True}


@pytest.mark.parametrize(
    "reason",
    [
        InterruptReason.WAIT,
        InterruptReason.TOOL_APPROVAL,
        InterruptReason.HOOK_GATE,
    ],
)
def test_interrupt_reason_serializes_stable_wire_strings(reason: InterruptReason):
    assert json.loads(json.dumps(reason)) == reason.value


def test_interrupt_reason_wait_is_distinct_from_tool_approval():
    assert InterruptReason.WAIT.value == "wait"
    assert InterruptReason.WAIT is not InterruptReason.TOOL_APPROVAL


def test_pending_approvals_ignores_wait_interrupts():
    """WAIT pauses are not human tool approvals; pending_approvals must skip them."""
    chat = {
        "id": "chat_1",
        "pending_interrupts": [
            {
                "id": "int_wait",
                "reason": InterruptReason.WAIT.value,
                "status": InterruptStatus.PENDING.value,
                "resource_id": "inv_wait",
            },
            {
                "id": "int_approve",
                "reason": InterruptReason.TOOL_APPROVAL.value,
                "status": InterruptStatus.PENDING.value,
                "resource_id": "inv_ok",
            },
        ],
    }
    got = pending_approvals(chat)
    assert len(got) == 1
    assert got[0].interrupt_id == "int_approve"
    assert got[0].tool_invocation_id == "inv_ok"
