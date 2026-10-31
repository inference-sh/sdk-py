"""Agent run and tool-invocation wire fields (cf09d41, fa5aa23).

``AgentRunDTO.finished_at`` is set when a run reaches a terminal state.
``ToolInvocationDTO.action`` is the model's imperative description of what
the call does (shown in agent UIs). These generated shapes must stay stable
for SDK clients parsing GET /agents/runs and tool-invocation payloads.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import (
    AgentRunDTO,
    AgentRunState,
    ToolInvocationDTO,
    ToolInvocationFunction,
    ToolInvocationStatus,
    ToolType,
)


def test_agent_run_dto_declares_finished_at():
    hints = get_type_hints(AgentRunDTO)
    assert hints["finished_at"] == Optional[str]


def test_agent_run_dto_finished_at_round_trips_when_terminal():
    run: AgentRunDTO = {
        "agent_id": "agt_1",
        "chat_id": "chat_1",
        "state": AgentRunState.COMPLETED,
        "finished_at": "2026-10-31T12:00:00Z",
    }
    wire = json.loads(json.dumps(run, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["state"] == "completed"
    assert wire["finished_at"] == "2026-10-31T12:00:00Z"


def test_agent_run_dto_omits_finished_at_while_working():
    run: AgentRunDTO = {
        "agent_id": "agt_1",
        "chat_id": "chat_1",
        "state": AgentRunState.WORKING,
    }
    wire = json.loads(json.dumps(run, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["state"] == "working"
    assert "finished_at" not in wire


def test_tool_invocation_dto_declares_action():
    hints = get_type_hints(ToolInvocationDTO)
    assert hints["action"] is str


def test_tool_invocation_dto_action_round_trips_on_wire():
    function: ToolInvocationFunction = {
        "name": "fetch_inbox",
        "arguments": '{"limit": 10}',
    }
    invocation: ToolInvocationDTO = {
        "chat_message_id": "msg_1",
        "tool_invocation_id": "tinv_1",
        "type": ToolType.HTTP,
        "display_name": "Fetch inbox",
        "action": "Fetch unread emails from alice@example.com",
        "function": function,
        "status": ToolInvocationStatus.IN_PROGRESS,
    }
    wire = json.loads(
        json.dumps(
            invocation,
            default=lambda o: o.value if hasattr(o, "value") else o,
        )
    )
    assert wire["action"] == "Fetch unread emails from alice@example.com"
    assert wire["type"] == "http"
    assert wire["status"] == "in_progress"


def test_tool_invocation_dto_allows_empty_action():
    invocation: ToolInvocationDTO = {
        "chat_message_id": "msg_2",
        "tool_invocation_id": "tinv_2",
        "type": ToolType.APP,
        "display_name": "Run app",
        "action": "",
        "status": ToolInvocationStatus.COMPLETED,
    }
    wire = json.loads(
        json.dumps(
            invocation,
            default=lambda o: o.value if hasattr(o, "value") else o,
        )
    )
    assert wire["action"] == ""
