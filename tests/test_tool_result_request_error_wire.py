"""ToolResultRequest.error wire contract (88139f6).

POST /tools/{id} bodies may include ``error`` when the client has no handler or
the handler failed; the run completes as failed and the model sees the error
text instead of ``result``. These tests lock the generated TypedDict shape SDK
clients rely on when reporting tool failures.
"""

import json
from typing import List, get_type_hints

import inferencesh
from inferencesh.types import FileRef, ToolResultRequest


def test_tool_result_request_declares_optional_error():
    hints = get_type_hints(ToolResultRequest)
    assert hints["error"] == str


def test_tool_result_request_keeps_result_and_attachments():
    hints = get_type_hints(ToolResultRequest)
    assert hints["result"] == str
    assert hints["attachments"] == List[FileRef]


def test_tool_result_request_error_round_trips_on_wire():
    body: ToolResultRequest = {
        "error": "no handler registered for tool 'browser.click'",
    }
    wire = json.loads(json.dumps(body))
    assert wire["error"] == "no handler registered for tool 'browser.click'"
    assert "result" not in wire

    parsed: ToolResultRequest = wire  # type: ignore[assignment]
    assert parsed["error"].startswith("no handler")


def test_tool_result_request_success_shape_unchanged():
    shot: FileRef = {
        "uri": "https://cloud.inference.sh/f/shot.png",
        "filename": "shot.png",
        "content_type": "image/png",
    }
    body: ToolResultRequest = {
        "result": '{"clicked": true}',
        "attachments": [shot],
    }
    wire = json.loads(json.dumps(body))
    assert wire["result"] == '{"clicked": true}'
    assert wire["attachments"][0]["filename"] == "shot.png"
    assert "error" not in wire


def test_tool_result_request_exported_from_package():
    assert hasattr(inferencesh, "ToolResultRequest")
    assert inferencesh.ToolResultRequest is ToolResultRequest
