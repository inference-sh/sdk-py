"""Chat and agent-run project_id wire contract (574ea6a).

New chats can be filed under a project via ``project_id`` on POST /agents/run
(when not continuing an existing ``chat_id``). Chat list/detail responses now
carry ``project_id`` / ``project`` through ``ProjectModelDTO`` on ``ChatDTO``.
These tests lock the generated TypedDict shape SDK clients rely on.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import (
    AgentDTO,
    ApiAgentRunRequest,
    ChatDTO,
    ChatStatus,
    MessageInput,
    ProjectDTO,
    ProjectModelDTO,
)


def test_api_agent_run_request_declares_optional_project_id():
    hints = get_type_hints(ApiAgentRunRequest)
    assert hints["project_id"] == Optional[str]


def test_chat_dto_inherits_project_model_fields():
    chat_hints = get_type_hints(ChatDTO)
    project_hints = get_type_hints(ProjectModelDTO)
    assert chat_hints["project_id"] == project_hints["project_id"]
    assert chat_hints["project"] == project_hints["project"]
    agent_hints = get_type_hints(AgentDTO)
    assert agent_hints["project_id"] == chat_hints["project_id"]


def test_api_agent_run_request_project_id_round_trips_on_wire():
    body: ApiAgentRunRequest = {
        "agent": "okaris/assistant@latest",
        "input": MessageInput(text="Plan the sprint"),
        "project_id": "proj_abc123",
    }
    wire = json.loads(json.dumps(body))
    assert wire["project_id"] == "proj_abc123"
    assert wire["input"]["text"] == "Plan the sprint"


def test_chat_dto_project_id_and_nested_project_round_trip():
    project: ProjectDTO = {
        "id": "proj_abc123",
        "name": "Platform",
        "description": "Core product work",
    }
    chat: ChatDTO = {
        "id": "chat_1",
        "status": ChatStatus.IDLE,
        "name": "Sprint planning",
        "description": "",
        "context": {},
        "agent_data": {},
        "work_dir": "/tmp/work",
        "project_id": "proj_abc123",
        "project": project,
    }
    wire = json.loads(json.dumps(chat))
    assert wire["project_id"] == "proj_abc123"
    assert wire["project"]["id"] == "proj_abc123"
    assert wire["project"]["name"] == "Platform"

    parsed: ChatDTO = wire  # type: ignore[assignment]
    assert parsed["project"]["name"] == "Platform"


def test_chat_dto_omits_project_when_unscoped():
    chat: ChatDTO = {
        "id": "chat_2",
        "status": ChatStatus.IDLE,
        "name": "Ad hoc",
        "description": "",
        "context": {},
        "agent_data": {},
        "work_dir": "/tmp/work",
    }
    wire = json.loads(json.dumps(chat))
    assert "project_id" not in wire
    assert "project" not in wire
