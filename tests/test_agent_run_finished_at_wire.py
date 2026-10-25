"""Agent run timing fields on API wire types (cf09d41 / api ef1de6deb).

``AgentRunDTO.finished_at`` is set when a run reaches a terminal state and is
absent while it is still active. ``ChatRunEvent.duration_ms`` on ``run_ended``
events records elapsed time from run start to end (the event message's
``created_at`` is when it ended).
"""

import json
from typing import get_type_hints

from inferencesh.types import (
    AgentRunDTO,
    AgentRunState,
    ChatDTO,
    ChatEvent,
    ChatEventType,
    ChatRunEvent,
    RunEndReason,
)


def test_agent_run_dto_exposes_finished_at_as_optional_timestamp():
    hints = get_type_hints(AgentRunDTO)
    assert hints["finished_at"] == str | None  # type: ignore[valid-type]
    assert hints["state"] is AgentRunState


def test_agent_run_dto_running_omits_finished_at():
    run: AgentRunDTO = {
        "agent_id": "agt_1",
        "chat_id": "chat_1",
        "state": AgentRunState.WORKING,
    }
    assert "finished_at" not in run
    assert run["state"] is AgentRunState.WORKING


def test_agent_run_dto_terminal_run_carries_finished_at():
    run: AgentRunDTO = {
        "agent_id": "agt_1",
        "chat_id": "chat_1",
        "state": AgentRunState.COMPLETED,
        "finished_at": "2026-10-25T19:20:34.123456Z",
        "output": {"reply": "done"},
    }
    assert run["finished_at"].endswith("Z")
    assert run["state"] is AgentRunState.COMPLETED


def test_chat_dto_active_run_inherits_finished_at_on_agent_run():
    hints = get_type_hints(ChatDTO)
    assert hints["active_run"] == AgentRunDTO | None  # type: ignore[valid-type]

    chat: ChatDTO = {
        "id": "chat_1",
        "name": "support",
        "description": "",
        "context": {},
        "chat_messages": [],
        "agent_data": {},
        "pending_interrupts": [],
        "work_dir": "/tmp",
        "active_run": {
            "agent_id": "agt_1",
            "chat_id": "chat_1",
            "state": AgentRunState.FAILED,
            "error": "upstream timeout",
            "finished_at": "2026-10-25T19:21:00Z",
        },
    }
    assert chat["active_run"]["finished_at"] == "2026-10-25T19:21:00Z"


def test_chat_run_event_exposes_duration_ms():
    hints = get_type_hints(ChatRunEvent)
    assert hints["duration_ms"] is int
    assert hints["run_id"] is str
    assert hints["reason"] is RunEndReason

    run_event: ChatRunEvent = {
        "run_id": "run_abc",
        "state": AgentRunState.COMPLETED,
        "reason": RunEndReason.NO_REPLY,
        "duration_ms": 842,
    }
    assert run_event["duration_ms"] == 842


def test_chat_event_run_ended_carries_duration_on_nested_run():
    event: ChatEvent = {
        "type": ChatEventType.RUN_ENDED,
        "run": {
            "run_id": "run_xyz",
            "state": AgentRunState.CANCELED,
            "reason": RunEndReason.OUTPUT_LIMIT,
            "duration_ms": 120_000,
        },
    }
    assert event["run"]["duration_ms"] == 120_000


def test_finished_at_and_duration_ms_use_snake_case_json_keys():
    payload = {
        "agent_id": "agt_1",
        "chat_id": "chat_1",
        "state": "completed",
        "finished_at": "2026-10-25T19:20:34Z",
    }
    wire = json.dumps(payload)
    assert '"finished_at"' in wire
    assert "finishedAt" not in wire

    ended = {
        "type": "run_ended",
        "run": {
            "run_id": "run_1",
            "state": "completed",
            "reason": "no_reply",
            "duration_ms": 99,
        },
    }
    ended_wire = json.dumps(ended)
    assert '"duration_ms"' in ended_wire
    assert "durationMs" not in ended_wire
