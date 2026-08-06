"""Unit tests for the V3 API Response envelope wrapper."""

from inferencesh.models.response import Response


def test_response_defaults_messages_to_empty_list():
    resp = Response({"id": "task_1"})
    assert resp.data == {"id": "task_1"}
    assert resp.messages == []


def test_response_has_warnings_true_for_warning_level():
    resp = Response(
        {"ok": True},
        messages=[
            {"level": "info", "message": "notice"},
            {"level": "warning", "code": "DEPRECATED", "message": "use v3"},
        ],
    )
    assert resp.has_warnings is True


def test_response_has_warnings_false_for_info_only():
    resp = Response(
        {"ok": True},
        messages=[{"level": "info", "message": "all good"}],
    )
    assert resp.has_warnings is False


def test_response_repr_omits_empty_messages():
    resp = Response({"id": "x"})
    assert repr(resp) == "Response(data={'id': 'x'})"


def test_response_repr_includes_messages_when_present():
    messages = [{"level": "warning", "message": "deprecated"}]
    resp = Response({"id": "x"}, messages=messages)
    assert repr(resp) == f"Response(data={{'id': 'x'}}, messages={messages})"
