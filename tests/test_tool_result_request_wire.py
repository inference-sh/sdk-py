"""ToolResultRequest.error wire contract (88139f6 typegen).

When a client cannot run a tool handler, POST /tools/{id} accepts ``error``
instead of ``result`` so the agent run completes as failed and the model reads
the failure text. These tests lock the generated request body shape SDK clients
and ``submit_tool_result`` callers rely on.
"""

import json
from typing import List, get_type_hints

from inferencesh.types import FileRef, ToolResultRequest


def test_tool_result_request_declares_result_attachments_and_error():
    hints = get_type_hints(ToolResultRequest)
    assert set(hints) == {"result", "attachments", "error"}
    assert hints["result"] is str
    assert hints["error"] is str
    assert hints["attachments"] == List[FileRef]


def test_tool_result_request_error_round_trips_on_wire():
    body: ToolResultRequest = {"error": "No handler registered for tool search_web"}
    wire = json.loads(json.dumps(body))
    assert wire == {"error": "No handler registered for tool search_web"}
    assert "result" not in wire
    parsed: ToolResultRequest = wire  # type: ignore[assignment]
    assert parsed["error"].startswith("No handler")


def test_tool_result_request_success_omits_error():
    body: ToolResultRequest = {"result": "done"}
    wire = json.loads(json.dumps(body))
    assert wire == {"result": "done"}
    assert "error" not in wire


def test_tool_result_request_with_attachments_and_result():
    shot: FileRef = {
        "uri": "https://cloud.inference.sh/f/shot.png",
        "filename": "shot.png",
        "content_type": "image/png",
    }
    body: ToolResultRequest = {"result": "screenshot captured", "attachments": [shot]}
    wire = json.loads(json.dumps(body))
    assert wire["result"] == "screenshot captured"
    assert wire["attachments"][0]["filename"] == "shot.png"
    assert "error" not in wire
