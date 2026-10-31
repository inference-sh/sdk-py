"""ChatDTO.origin and ChatOrigin wire contract (b7c6bd0).

Chat list/detail responses now carry ``origin`` (how the chat was created:
ui, api, trigger, integration, openai_client, embed, hook, subagent, branch).
``ChatData.client`` records the self-reported X-Client-Source app name for
display only. These tests lock the generated shapes SDK clients rely on when
filtering GET /chats and rendering chat metadata.
"""

import json
from typing import get_type_hints

from inferencesh.types import ChatDTO, ChatData, ChatOrigin, ChatStatus


def test_chat_origin_members_use_documented_wire_strings():
    assert ChatOrigin.UI.value == "ui"
    assert ChatOrigin.API.value == "api"
    assert ChatOrigin.TRIGGER.value == "trigger"
    assert ChatOrigin.INTEGRATION.value == "integration"
    assert ChatOrigin.OPEN_AI_CLIENT.value == "openai_client"
    assert ChatOrigin.EMBED.value == "embed"
    assert ChatOrigin.HOOK.value == "hook"
    assert ChatOrigin.SUBAGENT.value == "subagent"
    assert ChatOrigin.BRANCH.value == "branch"
    assert len(ChatOrigin) == 9


def test_chat_dto_declares_origin():
    hints = get_type_hints(ChatDTO)
    assert hints["origin"] is ChatOrigin


def test_chat_data_declares_client():
    hints = get_type_hints(ChatData)
    assert hints["client"] is str


def test_chat_dto_origin_round_trips_on_wire():
    for origin in ChatOrigin:
        chat: ChatDTO = {
            "id": f"chat_{origin.name.lower()}",
            "status": ChatStatus.IDLE,
            "name": "Example",
            "description": "",
            "context": {},
            "agent_data": {},
            "work_dir": "/tmp/work",
            "origin": origin,
        }
        wire = json.loads(json.dumps(chat))
        assert wire["origin"] == origin.value
        parsed: ChatDTO = wire  # type: ignore[assignment]
        assert parsed["origin"] == origin.value


def test_chat_dto_agent_data_client_round_trips_on_wire():
    chat: ChatDTO = {
        "id": "chat_web",
        "status": ChatStatus.IDLE,
        "name": "From mac app",
        "description": "",
        "context": {},
        "agent_data": {"client": "mac"},
        "work_dir": "/tmp/work",
        "origin": ChatOrigin.UI,
    }
    wire = json.loads(json.dumps(chat))
    assert wire["origin"] == "ui"
    assert wire["agent_data"]["client"] == "mac"
