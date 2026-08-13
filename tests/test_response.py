"""Unit tests for the V3 API Response envelope wrapper."""

from inferencesh.models.response import Response


class TestResponse:
    def test_data_and_empty_messages_by_default(self):
        resp = Response({"id": "task_1"})

        assert resp.data == {"id": "task_1"}
        assert resp.messages == []

    def test_has_warnings_true_only_for_warning_level(self):
        with_warning = Response(
            {"ok": True},
            [
                {"level": "info", "message": "note"},
                {"level": "warning", "code": "quota.low", "message": "approaching limit"},
            ],
        )
        info_only = Response({"ok": True}, [{"level": "info", "message": "note"}])

        assert with_warning.has_warnings is True
        assert info_only.has_warnings is False

    def test_repr_omits_messages_when_empty(self):
        assert repr(Response({"id": "x"})) == "Response(data={'id': 'x'})"

    def test_repr_includes_messages_when_present(self):
        messages = [{"level": "warning", "message": "quota low"}]
        resp = Response({"id": "x"}, messages)

        assert repr(resp) == f"Response(data={{'id': 'x'}}, messages={messages})"
