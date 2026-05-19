"""Unit tests for client status helpers and stream event processing."""

import pytest

from inferencesh import (
    ChatMessageStatus,
    TaskStatus,
    is_message_ready,
    is_terminal_status,
    parse_status,
)
from inferencesh.client import _process_stream_event


class TestParseStatus:
    def test_none_returns_none(self):
        assert parse_status(None) is None

    def test_int_valid_status(self):
        assert parse_status(7) == TaskStatus.RUNNING
        assert parse_status(10) == TaskStatus.COMPLETED

    def test_int_invalid_returns_unknown(self):
        assert parse_status(999) == TaskStatus.UNKNOWN

    def test_string_status_names(self):
        assert parse_status("running") == TaskStatus.RUNNING
        assert parse_status("COMPLETED") == TaskStatus.COMPLETED

    def test_unknown_string_returns_unknown(self):
        assert parse_status("not-a-real-status") == TaskStatus.UNKNOWN

    def test_non_int_non_str_returns_unknown(self):
        assert parse_status([]) == TaskStatus.UNKNOWN


class TestIsTerminalStatus:
    def test_completed_is_terminal(self):
        assert is_terminal_status(TaskStatus.COMPLETED) is True
        assert is_terminal_status("completed") is True
        assert is_terminal_status(10) is True

    def test_running_is_not_terminal(self):
        assert is_terminal_status(TaskStatus.RUNNING) is False
        assert is_terminal_status("running") is False

    def test_none_is_not_terminal(self):
        assert is_terminal_status(None) is False


class TestIsMessageReady:
    def test_pending_is_not_ready(self):
        assert is_message_ready(ChatMessageStatus.PENDING) is False
        assert is_message_ready("pending") is False

    def test_ready_is_terminal(self):
        assert is_message_ready(ChatMessageStatus.READY) is True
        assert is_message_ready("ready") is True

    def test_failed_and_cancelled_are_ready(self):
        assert is_message_ready("failed") is True
        assert is_message_ready("cancelled") is True

    def test_empty_or_none_is_pending(self):
        assert is_message_ready(None) is False
        assert is_message_ready("") is False


class TestProcessStreamEvent:
    def test_completed_returns_stripped_task(self):
        task = {"id": "t1", "extra": "ignored"}
        data = {
            "id": "t1",
            "status": TaskStatus.COMPLETED,
            "output": {"ok": True},
            "extra": "ignored",
        }
        stopper_calls = []

        result = _process_stream_event(
            data,
            task=task,
            stopper=lambda: stopper_calls.append(1),
        )

        assert result is not None
        assert result["output"] == {"ok": True}
        assert "extra" not in result
        assert stopper_calls == [1]

    def test_failed_raises_with_error_message(self):
        with pytest.raises(RuntimeError, match="boom"):
            _process_stream_event(
                {"status": TaskStatus.FAILED, "error": "boom"},
                task={},
            )

    def test_cancelled_raises(self):
        with pytest.raises(RuntimeError, match="cancelled"):
            _process_stream_event(
                {"status": TaskStatus.CANCELLED},
                task={},
            )

    def test_non_terminal_returns_none(self):
        assert _process_stream_event(
            {"status": TaskStatus.RUNNING},
            task={},
        ) is None
