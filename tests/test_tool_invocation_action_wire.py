"""ToolInvocationDTO.action on API wire types (fa5aa23 / api 6bf95f16d).

``action`` is the imperative phrase the model attached to a tool call
("Fetch unread emails from alice@x.com"). The API sends an empty string when
the model omitted a phrase; clients use it for UI labels alongside
``display_name``.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    ChatMessageDTO,
    ChatMessageRole,
    ChatMessageStatus,
    ToolInvocationDTO,
    ToolInvocationStatus,
    ToolType,
)


def test_tool_invocation_dto_exposes_action_as_string():
    hints = get_type_hints(ToolInvocationDTO)
    assert hints["action"] is str
    assert hints["display_name"] is str
    assert hints["status"] is ToolInvocationStatus


def test_tool_invocation_with_model_action_phrase():
    inv: ToolInvocationDTO = {
        "tool_invocation_id": "inv_1",
        "chat_message_id": "msg_1",
        "type": ToolType.CLIENT,
        "display_name": "search_mail",
        "action": "Fetch unread emails from alice@example.com",
        "status": ToolInvocationStatus.AWAITING_INPUT,
        "function": {"name": "search_mail", "arguments": {"from": "alice@example.com"}},
    }
    assert inv["action"].startswith("Fetch unread")
    assert inv["display_name"] == "search_mail"


def test_tool_invocation_action_empty_when_model_omitted_phrase():
    inv: ToolInvocationDTO = {
        "tool_invocation_id": "inv_2",
        "type": ToolType.MCP,
        "display_name": "run_sql",
        "action": "",
        "status": ToolInvocationStatus.COMPLETED,
        "function": {"name": "run_sql", "arguments": {"query": "select 1"}},
    }
    assert inv["action"] == ""


def test_tool_invocation_action_key_may_be_absent_on_partial_payload():
    """total=False allows streaming deltas without every field."""
    inv: ToolInvocationDTO = {
        "tool_invocation_id": "inv_3",
        "type": ToolType.CLIENT,
        "status": ToolInvocationStatus.IN_PROGRESS,
        "function": {"name": "deploy", "arguments": {}},
    }
    assert "action" not in inv


def test_chat_message_dto_tool_invocations_carry_action():
    hints = get_type_hints(ChatMessageDTO)
    assert hints["tool_invocations"] == Optional[List[ToolInvocationDTO]]

    message: ChatMessageDTO = {
        "chat_id": "chat_1",
        "order": 3,
        "status": ChatMessageStatus.READY,
        "role": ChatMessageRole.ASSISTANT,
        "content": [],
        "tool_invocations": [
            {
                "tool_invocation_id": "inv_9",
                "type": ToolType.MCP,
                "display_name": "list_buckets",
                "action": "List S3 buckets in us-east-1",
                "status": ToolInvocationStatus.COMPLETED,
                "function": {"name": "list_buckets", "arguments": {"region": "us-east-1"}},
            }
        ],
    }
    assert message["tool_invocations"][0]["action"] == "List S3 buckets in us-east-1"


def test_action_uses_snake_case_json_key():
    payload = {
        "tool_invocation_id": "inv_json",
        "type": "client",
        "display_name": "ask_user",
        "action": "Ask the user for their API key",
        "status": "awaiting_input",
        "function": {"name": "ask_user", "arguments": {}},
    }
    wire = json.dumps(payload)
    assert '"action"' in wire
    assert "Action" not in wire
