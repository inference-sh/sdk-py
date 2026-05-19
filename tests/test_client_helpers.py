"""Unit tests for client task/stream helpers (high blast-radius, no I/O)."""

import pytest

from inferencesh import TaskStatus
from inferencesh.client import (
    _looks_like_base64,
    _process_stream_event,
    _strip_task,
)


class TestStripTask:
    def test_keeps_essential_fields_only(self):
        raw = {
            "id": "task_1",
            "status": 10,
            "input": {"x": 1},
            "output": {"y": 2},
            "logs": ["done"],
            "created_at": "2026-01-01",
            "updated_at": "2026-01-02",
            "worker_id": "w-99",
            "internal_trace": "secret",
        }
        stripped = _strip_task(raw)
        assert stripped == {
            "id": "task_1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-02",
            "input": {"x": 1},
            "output": {"y": 2},
            "logs": ["done"],
            "status": 10,
        }
        assert "worker_id" not in stripped
        assert "internal_trace" not in stripped

    def test_includes_session_id_when_present(self):
        stripped = _strip_task({
            "id": "task_1",
            "status": 1,
            "session_id": "sess_abc",
            "extra": "ignored",
        })
        assert stripped["session_id"] == "sess_abc"
        assert "extra" not in stripped


class TestLooksLikeBase64:
    def test_rejects_short_strings(self):
        assert _looks_like_base64("aGVsbG8=") is False  # too short
        assert _looks_like_base64("hello") is False

    def test_rejects_plain_text_that_matches_charset(self):
        # Long enough but not valid base64 payload
        assert _looks_like_base64("this-is-not-base64-data!!") is False

    def test_accepts_valid_base64(self):
        # "hello world" in base64, padded to length multiple of 4
        payload = "aGVsbG8gd29ybGQ="
        assert _looks_like_base64(payload) is True


class TestProcessStreamEvent:
    def test_completed_returns_stripped_task_and_calls_stopper(self):
        stopper_called = []

        result = _process_stream_event(
            {"id": "t1", "status": TaskStatus.COMPLETED, "output": {"ok": True}, "noise": 1},
            task={},
            stopper=lambda: stopper_called.append(1),
        )

        assert result == {
            "id": "t1",
            "created_at": None,
            "updated_at": None,
            "input": None,
            "output": {"ok": True},
            "logs": None,
            "status": TaskStatus.COMPLETED,
        }
        assert stopper_called == [1]

    def test_failed_raises_and_calls_stopper(self):
        stopper_called = []

        with pytest.raises(RuntimeError, match="boom"):
            _process_stream_event(
                {"status": TaskStatus.FAILED, "error": "boom"},
                task={},
                stopper=lambda: stopper_called.append(1),
            )

        assert stopper_called == [1]

    def test_cancelled_raises_default_message(self):
        with pytest.raises(RuntimeError, match="cancelled"):
            _process_stream_event(
                {"status": TaskStatus.CANCELLED},
                task={},
            )

    def test_non_terminal_returns_none(self):
        assert _process_stream_event(
            {"status": TaskStatus.RUNNING, "id": "t1"},
            task={},
        ) is None
