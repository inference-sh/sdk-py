"""Unit tests for agent chat stream routing (_ChatStreamRouter).

Deltas without a resource_id cannot be attributed to a message and must be
dropped so a tool-only turn does not show the previous assistant message text.
"""

from inferencesh.agent import _ChatStreamRouter
from inferencesh.types import ChatMessageStatus, ToolInvocationStatus, ToolType


def test_delta_dropped_without_resource_id():
    router = _ChatStreamRouter(set())
    assert router.delta({"delta": {"response": "orphan"}, "seq": 1}) is None


def test_delta_dropped_when_payload_missing():
    router = _ChatStreamRouter(set())
    assert router.delta({"resource_id": "msg_1", "seq": 1}) is None
    assert router.delta({"resource_id": "", "delta": {"response": "x"}, "seq": 1}) is None


def test_delta_accumulates_per_message_id():
    router = _ChatStreamRouter(set())

    first = router.delta(
        {"resource_id": "asst-1", "delta": {"response": "Hel"}, "seq": 1},
    )
    second = router.delta(
        {"resource_id": "asst-1", "delta": {"response": "lo"}, "seq": 2},
    )
    other = router.delta(
        {"resource_id": "asst-2", "delta": {"response": "Other"}, "seq": 1},
    )

    assert first is not None and first.output["response"] == "Hel"
    assert second is not None and second.output["response"] == "Hello"
    assert other is not None and other.output["response"] == "Other"


def test_terminal_message_clears_delta_accumulator_for_that_message():
    router = _ChatStreamRouter(set())

    router.delta({"resource_id": "asst-1", "delta": {"response": "partial"}, "seq": 1})
    router.message(
        {
            "id": "asst-1",
            "status": ChatMessageStatus.READY,
            "text": "partial",
            "role": "assistant",
        },
        dispatch_tools=False,
    )

    fresh = router.delta(
        {"resource_id": "asst-1", "delta": {"response": "new"}, "seq": 2},
    )
    assert fresh is not None and fresh.output["response"] == "new"


def test_message_dispatches_client_tool_only_once():
    router = _ChatStreamRouter(set())
    inv = {
        "id": "inv_1",
        "type": ToolType.CLIENT,
        "status": ToolInvocationStatus.AWAITING_INPUT,
        "function": {"name": "confirm", "arguments": {"ok": True}},
    }

    first = router.message({"tool_invocations": [inv]}, dispatch_tools=True)
    second = router.message({"tool_invocations": [inv]}, dispatch_tools=True)

    assert len(first) == 1 and first[0].name == "confirm"
    assert second == []
